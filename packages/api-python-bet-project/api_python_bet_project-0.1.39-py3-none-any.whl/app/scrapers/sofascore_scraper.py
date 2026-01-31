import re
import time
from typing import Optional, List, Dict, Any

import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


MATCH_LINKS_CSS = "a[class*='event-hl-'][href*='/match/']"


class SofaScoreScraper:
    """
    SofaScore match scraper (By round / gameweek).

    Output columns:
      - gameweek: int
      - date: str (dd/mm/yy) if available, else ""
      - link: str (match URL)

    Notes:
      - Round navigation is done via the "Round X" dropdown (virtualized list).
      - If a match appears twice in the same round (e.g., postponed/relisted),
        the scraper keeps the second occurrence (last seen in DOM).
    """

    def __init__(self, headless: bool = True, verbose: bool = True):
        """
        Args:
            headless: Run Chrome headless.
            verbose: If True, prints logs to stdout. If False, stays silent.
        """
        self.headless = headless
        self.verbose = verbose
        self.driver = None

    # ---------------------------------------------------------------------
    # Logging
    # ---------------------------------------------------------------------
    def _log(self, msg: str, level: str = "INFO") -> None:
        """Print log messages when verbose is enabled."""
        if not self.verbose:
            return
        prefix = {
            "INFO": "[INFO]",
            "SUCCESS": "[OK]",
            "WARNING": "[WARN]",
            "ERROR": "[ERROR]",
            "DEBUG": "[DEBUG]",
        }.get(level, "[INFO]")
        print(f"{prefix} {msg}")

    # ---------------------------------------------------------------------
    # Driver setup
    # ---------------------------------------------------------------------
    def _setup_driver(self) -> None:
        """Create and configure a Chrome WebDriver instance."""
        options = Options()
        if self.headless:
            options.add_argument("--headless=new")

        # Reduce automation detection noise (not bulletproof)
        options.add_argument("--disable-blink-features=AutomationControlled")

        # Useful for some Linux environments / CI
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        options.add_argument(f"--user-agent={user_agent}")

        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1600, 1000)

        # Force UA at the network layer too
        self.driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": user_agent})

    # ---------------------------------------------------------------------
    # Low-level helpers
    # ---------------------------------------------------------------------
    def _click(self, el) -> None:
        """Click via JS (helps when normal click is intercepted)."""
        self.driver.execute_script("arguments[0].click();", el)

    def _close_popups(self) -> None:
        """Close cookie consent and other popups (best-effort)."""
        selectors = [
            "button.fc-button.fc-cta-consent",
            "//button[contains(., 'Consent')]",
            "//button[contains(., 'Accept')]",
            "//button[contains(., 'Aceptar')]",
            "//button[contains(., 'Tout accepter')]",
        ]
        for selector in selectors:
            try:
                if selector.startswith("//"):
                    btn = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    btn = WebDriverWait(self.driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                self._click(btn)
                time.sleep(0.6)
                break
            except Exception:
                continue

        # Generic close button (sometimes used by modals)
        try:
            close_btn = WebDriverWait(self.driver, 1).until(
                EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Close']"))
            )
            self._click(close_btn)
            time.sleep(0.3)
        except Exception:
            pass

    def _wait_matches_present(self, timeout: int = 20) -> None:
        """Wait until at least one match link is visible in the DOM."""
        WebDriverWait(self.driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, MATCH_LINKS_CSS)) > 0
        )

    def _wait_matches_refresh(self, old_links: set[str], timeout: int = 15) -> None:
        """
        Wait until the match list changes compared to old_links.
        More reliable than staleness_of in React UIs (nodes can be reused).
        """

        def _current_links() -> set[str]:
            elems = self.driver.find_elements(By.CSS_SELECTOR, MATCH_LINKS_CSS)
            return {e.get_attribute("href") for e in elems if e.get_attribute("href")}

        WebDriverWait(self.driver, timeout).until(lambda d: len(_current_links()) > 0)
        WebDriverWait(self.driver, timeout).until(lambda d: _current_links() != old_links)

    # ---------------------------------------------------------------------
    # Tabs + season selection
    # ---------------------------------------------------------------------
    def _click_matches_tab(self) -> None:
        """Ensure the Matches tab is selected (best-effort)."""
        try:
            tab = self.driver.find_element(By.CSS_SELECTOR, "[data-testid='tab-matches']")
            self._click(tab)
            time.sleep(0.8)
        except Exception:
            pass

    def _select_season(self, season: str) -> bool:
        """Select a season from the dropdown (best-effort)."""
        try:
            self._log(f"Selecting season: {season}", "INFO")

            dropdown_btn = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button.dropdown__button"))
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", dropdown_btn)
            time.sleep(0.3)
            self._click(dropdown_btn)
            time.sleep(0.8)

            items = self.driver.find_elements(By.CSS_SELECTOR, "li.dropdown__listItem")
            for item in items:
                if season in (item.text or "").strip():
                    self._click(item)
                    time.sleep(1.5)
                    self._log(f"Season {season} selected", "SUCCESS")
                    return True

            self._log(f"Season '{season}' not found in dropdown list.", "WARNING")
            return False

        except Exception as e:
            self._log(f"Error selecting season: {e}", "ERROR")
            return False

    def _click_by_round_tab_strict(self) -> None:
        """
        Ensure the page is in 'By round' mode and the 'Round X' dropdown exists.
        """
        # Click the "By round" pill if present
        try:
            by_round = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[normalize-space()='By round']"))
            )
            self._click(by_round)
            time.sleep(0.6)
        except Exception:
            # Not fatal if already in the correct mode
            pass

        # Verify the "Round X" dropdown button exists
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@class,'dropdown__button') and contains(., 'Round')]")
            )
        )
        self._log("'By round' UI detected (round dropdown button found).", "SUCCESS")

    # ---------------------------------------------------------------------
    # Round dropdown navigation (virtualized list)
    # ---------------------------------------------------------------------
    def _open_round_dropdown(self) -> None:
        """Open the dropdown showing the round list (button with 'Round X')."""
        wait = WebDriverWait(self.driver, 10)
        round_btn = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(@class,'dropdown__button') and contains(., 'Round')]")
            )
        )
        self._click(round_btn)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.dropdown__listContainer")))
        time.sleep(0.2)

    def _get_round_list_scroll_container(self):
        """
        Return the element to scroll inside the dropdown.
        SofaScore uses a custom scrollbar container for virtualized lists.
        """
        wait = WebDriverWait(self.driver, 10)

        containers = self.driver.find_elements(By.CSS_SELECTOR, "div.beautiful-scrollbar__container")
        if containers:
            return containers[0]

        return wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.dropdown__listContainer")))

    def _select_round_from_dropdown(self, target_round: int, max_scroll_steps: int = 80) -> bool:
        """
        Select a round from the dropdown list.
        The list is virtualized: older rounds are not in DOM until you scroll.
        """
        label = f"Round {target_round}"

        self._open_round_dropdown()
        scroll_el = self._get_round_list_scroll_container()

        def _try_click_item() -> bool:
            items = self.driver.find_elements(By.CSS_SELECTOR, "li.dropdown__listItem")
            for it in items:
                if (it.text or "").strip() == label:
                    self._click(it)
                    return True
            return False

        # Try without scrolling
        if _try_click_item():
            return True

        # Scroll up until the target appears
        for step in range(max_scroll_steps):
            if step in (0, 5, 10):
                self.driver.execute_script("arguments[0].scrollTop = 0;", scroll_el)
            else:
                self.driver.execute_script(
                    "arguments[0].scrollTop = Math.max(0, arguments[0].scrollTop - 450);",
                    scroll_el,
                )
            time.sleep(0.12)

            if _try_click_item():
                return True

        # Close dropdown (best-effort)
        try:
            self.driver.execute_script("document.body.click();")
        except Exception:
            pass

        return False

    def _get_current_round_num(self) -> Optional[int]:
        """Parse the current round number from the dropdown button text (e.g., 'Round 38')."""
        try:
            btn = self.driver.find_element(
                By.XPATH, "//button[contains(@class,'dropdown__button') and contains(., 'Round')]"
            )
            txt = (btn.text or "").strip()
            m = re.search(r"Round\s*([0-9]{1,3})", txt, re.IGNORECASE)
            return int(m.group(1)) if m else None
        except Exception:
            return None

    def _go_to_round_via_dropdown(self, target_round: int) -> bool:
        """
        Navigate to a specific round using the dropdown and wait for UI refresh.
        """
        cur = self._get_current_round_num()
        if cur == target_round:
            return True

        # Snapshot current links to detect refresh
        old_links = set()
        for e in self.driver.find_elements(By.CSS_SELECTOR, MATCH_LINKS_CSS):
            href = e.get_attribute("href")
            if href:
                old_links.add(href)

        ok = self._select_round_from_dropdown(target_round=target_round, max_scroll_steps=180)
        if not ok:
            return False

        # Prefer round label update
        try:
            WebDriverWait(self.driver, 12).until(lambda d: self._get_current_round_num() == target_round)
        except Exception:
            pass

        # Then ensure match list actually changes
        try:
            self._wait_matches_refresh(old_links=old_links, timeout=18)
        except Exception:
            # Fallback: ensure links exist
            try:
                self._wait_matches_present(timeout=10)
            except Exception:
                pass

        time.sleep(0.2)
        return True

    # ---------------------------------------------------------------------
    # Scraping (gameweek, date, link)
    # ---------------------------------------------------------------------
    def _scrape_current_round(self, gameweek: int) -> List[Dict]:
        """
        Extract match rows for the current round.

        Returns:
          - gameweek (int)
          - date (dd/mm/yy) or empty string if missing
          - link (full match URL)

        Deduplication rule:
          If the same match appears twice in this round, keep the second one.
        """
        time.sleep(0.6)

        link_elems = self.driver.find_elements(By.CSS_SELECTOR, MATCH_LINKS_CSS)
        self._log(f"Found {len(link_elems)} match links in DOM", "DEBUG")

        date_re = re.compile(r"\b(\d{2}/\d{2}/\d{2})\b")

        def _base_link(href: str) -> str:
            return href.split("#", 1)[0].strip()

        def _extract_date(a) -> str:
            texts: List[str] = []

            for attr in ("innerText", "textContent"):
                try:
                    t = (a.get_attribute(attr) or "").strip()
                    if t:
                        texts.append(t)
                except Exception:
                    pass

            try:
                for el in a.find_elements(By.XPATH, ".//*"):
                    for attr in ("title", "aria-label"):
                        v = (el.get_attribute(attr) or "").strip()
                        if v:
                            texts.append(v)
            except Exception:
                pass

            blob = "\n".join(texts)
            m = date_re.search(blob)
            return m.group(1) if m else ""

        by_key: Dict[str, Dict] = {}
        order: List[str] = []

        for a in link_elems:
            try:
                href = a.get_attribute("href")
                if not href:
                    continue

                key = _base_link(href)

                row = {
                    "gameweek": gameweek,
                    "date_of_match": _extract_date(a),
                    "link": href,
                }

                if key not in by_key:
                    order.append(key)

                # Overwrite => keep last (second) occurrence
                by_key[key] = row

            except Exception as e:
                self._log(f"Error extracting match: {e}", "DEBUG")

        return [by_key[k] for k in order]

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------
    def scrape_gameweeks(
        self,
        url: str,
        season: str = None,
        max_rounds: int = 38,
        target_dates: Optional[List[str]] = None,
    ) -> pd.DataFrame:
        """
        Scrape all gameweeks from 1..max_rounds (inclusive) and return a DataFrame.

        Args:
            url: SofaScore league matches URL.
            season: Season label as shown in UI (e.g., "24/25"). If None, keeps current.
            max_rounds: Max gameweek to scrape (inclusive).
            target_dates: Optional list of dates ("dd/mm/yy"). If provided, returns only
                        matches whose `date` is in this list.
        """
        self._log("=" * 70, "INFO")
        self._log("SOFASCORE SCRAPER", "INFO")
        self._log(f"Season: {season or 'current'}", "INFO")
        self._log(f"Max rounds: {max_rounds}", "INFO")
        if target_dates:
            self._log(f"Filtering by dates: {target_dates}", "INFO")
        self._log("=" * 70, "INFO")

        all_matches: List[Dict] = []

        try:
            self._setup_driver()
            self.driver.get(url)
            time.sleep(3)

            self._close_popups()

            if season:
                self._select_season(season)
                time.sleep(2)

            try:
                self._wait_matches_present(timeout=20)
            except Exception:
                pass

            self._click_matches_tab()
            self._close_popups()

            self._log("Selecting 'By round' mode (strict).", "INFO")
            self._click_by_round_tab_strict()

            self._log("Ensuring we are on Round 1.", "INFO")
            if not self._go_to_round_via_dropdown(1):
                raise RuntimeError("Could not navigate to Round 1 via dropdown.")

            for gw in range(1, max_rounds + 1):
                if gw != 1:
                    self._log(f"Navigating to Round {gw}.", "INFO")
                    if not self._go_to_round_via_dropdown(gw):
                        self._log(f"Cannot navigate to Round {gw} via dropdown.", "WARNING")
                        break

                self._log(f"Scraping Round {gw}.", "INFO")
                rows = self._scrape_current_round(gameweek=gw)
                all_matches.extend(rows)
                self._log(f"Round {gw}: {len(rows)} matches", "SUCCESS")

            df = pd.DataFrame(all_matches)
            if df.empty:
                return df

            # Deduplicate and standardize
            df = df.drop_duplicates(subset=["link"]).reset_index(drop=True)

            # ---- FILTER BY TARGET DATES (if provided) ----
            if target_dates:
                target_set = {d.strip() for d in target_dates if d and str(d).strip()}
                df = df[df["date_of_match"].isin(target_set)].reset_index(drop=True)

            self._log("=" * 70, "INFO")
            self._log(f"Total matches (after filter): {len(df)}", "SUCCESS")
            self._log("=" * 70, "INFO")
            return df

        except Exception as e:
            self._log(f"Error: {e}", "ERROR")
            import traceback
            self._log(traceback.format_exc(), "DEBUG")

            # Return partial results if available (also filtered if requested)
            df = pd.DataFrame(all_matches)
            if not df.empty:
                df = df.drop_duplicates(subset=["link"]).reset_index(drop=True)
                if target_dates:
                    target_set = {d.strip() for d in target_dates if d and str(d).strip()}
                    df = df[df["date_of_match"].isin(target_set)].reset_index(drop=True)
            return df

    def _abs_url(self, url: str) -> str:
        """Ensure SofaScore absolute URL."""
        if url.startswith("http"):
            return url
        return "https://www.sofascore.com" + url


    def _extract_match_header_info(self) -> Dict[str, str]:
        """
        Extract match header information with precise team detection.
        """
        wait = WebDriverWait(self.driver, 15)
        wait.until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "a[href*='/football/team/']")
        )
        time.sleep(1)
        
        home_team_name = ""
        away_team_name = ""
        hour_of_the_match = ""
        
        # === STRATEGY: Find teams in header container ===
        try:
            # Look for team links that are likely in the match header
            # Typically these have the team logo/image nearby
            team_links_with_images = self.driver.find_elements(
                By.XPATH,
                "//main//a[contains(@href, '/football/team/') and .//img]"
            )
            
            if len(team_links_with_images) >= 2:
                # Extract using JavaScript to get clean text
                home_team_name = self.driver.execute_script(
                    """
                    var elem = arguments[0];
                    // Get text from immediate text nodes, skip nested elements
                    var text = '';
                    for (var i = 0; i < elem.childNodes.length; i++) {
                        var node = elem.childNodes[i];
                        if (node.nodeType === 3) {  // TEXT_NODE
                            text += node.textContent;
                        }
                    }
                    return text.trim();
                    """,
                    team_links_with_images[0]
                ).strip()
                
                away_team_name = self.driver.execute_script(
                    """
                    var elem = arguments[0];
                    var text = '';
                    for (var i = 0; i < elem.childNodes.length; i++) {
                        var node = elem.childNodes[i];
                        if (node.nodeType === 3) {
                            text += node.textContent;
                        }
                    }
                    return text.trim();
                    """,
                    team_links_with_images[1]
                ).strip()
            
            # Fallback: If names are empty or look wrong, extract from href
            if not home_team_name or home_team_name == "Compare teams":
                href = team_links_with_images[0].get_attribute("href")
                home_team_name = href.split("/football/team/")[1].split("/")[0]
                home_team_name = home_team_name.replace("-", " ").title()
            
            if not away_team_name or away_team_name == "Compare teams":
                href = team_links_with_images[1].get_attribute("href")
                away_team_name = href.split("/football/team/")[1].split("/")[0]
                away_team_name = away_team_name.replace("-", " ").title()
            
        except Exception as e:
            self._log(f"Error extracting teams: {e}", "WARNING")
        
        # === Extract time ===
        time_re = re.compile(r"\b(\d{1,2}:\d{2})\b")
        
        try:
            main = self.driver.find_element(By.TAG_NAME, "main")
            blob = main.get_attribute("innerText") or ""
            
            m = time_re.search(blob)
            if m:
                hh, mm = m.group(1).split(":")
                hour_of_the_match = f"{int(hh):02d}:{int(mm):02d}"
                
        except Exception as e:
            self._log(f"Error extracting time: {e}", "WARNING")
        
        return {
            "home_team_name": home_team_name,
            "away_team_name": away_team_name,
            "hour_of_the_match": hour_of_the_match,
        }
    
    def navigate_to_section(
        self, 
        section_name: str,
        wait_time: float = 1.0
    ) -> Dict[str, Any]:
        """
        Navigate to a specific section (tab) in the match page.
        
        Args:
            section_name: Name of section (e.g., "Statistics", "Lineups", "H2H")
            wait_time: Time to wait after clicking
        
        Returns:
            Dict with success status and section info
        """
        
        wait = WebDriverWait(self.driver, 15)
        
        result = {
            "success": False,
            "section_name": section_name,
            "error": None
        }
        
        try:
            # Wait for page to load
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "main")))
            time.sleep(0.5)
            
            # Find all clickable tabs/buttons
            tab_buttons = self.driver.find_elements(
                By.XPATH,
                "//main//button[contains(., 'Statistics')] | "
                "//main//a[contains(., 'Statistics')] | "
                f"//main//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{section_name.lower()}')] | "
                f"//main//a[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{section_name.lower()}')]"
            )
            
            target_button = None
            
            for btn in tab_buttons:
                btn_text = (btn.text or "").strip().lower()
                if section_name.lower() in btn_text:
                    target_button = btn
                    break
            
            if target_button:
                # Scroll into view and click
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});",
                    target_button
                )
                time.sleep(0.3)
                
                try:
                    target_button.click()
                except Exception:
                    # Fallback: JavaScript click
                    self.driver.execute_script("arguments[0].click();", target_button)
                
                time.sleep(wait_time)
                
                result["success"] = True
                self._log(f"Navigated to: {section_name}", "SUCCESS")
            else:
                self._log(f"Tab '{section_name}' not found", "WARNING")
                result["error"] = f"Tab '{section_name}' not found"
        
        except Exception as e:
            self._log(f"Error navigating to {section_name}: {e}", "ERROR")
            result["error"] = str(e)
        
        return result
    
    def extract_match_statistics(self, wait_time: float = 1.5) -> Dict[str, Any]:
        """
        Extract all match statistics from the Statistics tab.
        
        Returns dict with:
        - home_stats: dict with all home team statistics
        - away_stats: dict with all away team statistics
        - stat_names: list of statistic names
        """
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(self.driver, 15)
        
        result = {
            "success": False,
            "home_stats": {},
            "away_stats": {},
            "stat_names": [],
            "error": None
        }
        
        try:
            # Wait for statistics to load
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "bg_surface_s1"))
            )
            time.sleep(wait_time)
            
            # Find all statistic rows
            # Each row has structure: home_value | stat_name | away_value
            stat_rows = self.driver.find_elements(
                By.XPATH,
                "//div[contains(@class, 'd_flex') and contains(@class, 'ai_center') and contains(@class, 'jc_center')]"
                "[.//bdi[@aria-describedby] or .//bdi[contains(@class, 'w_fit')]]"
            )
            
            if not stat_rows:
                # Alternative selector for stat rows
                stat_rows = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'd_flex') and .//span[contains(@class, 'textStyle_assistive')]]"
                )
            
            self._log(f"Found {len(stat_rows)} statistic rows", "INFO")
            
            stats_data = []
            
            for row in stat_rows:
                try:
                    # Extract the statistic name (center element)
                    stat_name_elem = row.find_elements(
                        By.XPATH,
                        ".//bdi[contains(@class, 'w_fit')]//bdi | "
                        ".//bdi[@aria-describedby] | "
                        ".//span[contains(text(), 'possession') or contains(text(), 'goals') or "
                        "contains(text(), 'shots') or contains(text(), 'Shots') or "
                        "contains(text(), 'passes') or contains(text(), 'Passes')]"
                    )
                    
                    if not stat_name_elem:
                        continue
                    
                    stat_name = stat_name_elem[0].text.strip()
                    
                    if not stat_name:
                        continue
                    
                    # Extract home value (left side)
                    home_value_elems = row.find_elements(
                        By.XPATH,
                        ".//bdi[contains(@class, 'fa_start') or contains(@class, 'flex_[1_1_0px]')][1]"
                        "//span[contains(@class, 'textStyle_assistive') or contains(@class, 'textStyle_table')]"
                    )
                    
                    home_value = ""
                    if home_value_elems:
                        home_value = home_value_elems[0].text.strip()
                    
                    # Extract away value (right side)
                    away_value_elems = row.find_elements(
                        By.XPATH,
                        ".//bdi[contains(@class, 'ta_end') or contains(@class, 'flex_[1_1_0px]')][last()]"
                        "//span[contains(@class, 'textStyle_assistive') or contains(@class, 'textStyle_table')]"
                    )
                    
                    away_value = ""
                    if away_value_elems:
                        away_value = away_value_elems[0].text.strip()
                    
                    # Only add if we have valid data
                    if stat_name and (home_value or away_value):
                        stats_data.append({
                            "stat_name": stat_name,
                            "home_value": home_value,
                            "away_value": away_value
                        })
                        
                        self._log(
                            f"  {stat_name}: {home_value} - {away_value}",
                            "DEBUG"
                        )
                
                except Exception as e:
                    self._log(f"Error parsing stat row: {e}", "DEBUG")
                    continue
            
            # Organize into dictionaries
            home_stats = {}
            away_stats = {}
            stat_names = []
            
            for stat in stats_data:
                # Clean stat name for use as key
                key = stat["stat_name"].lower().replace(" ", "_").replace("(", "").replace(")", "")
                
                home_stats[key] = stat["home_value"]
                away_stats[key] = stat["away_value"]
                stat_names.append(stat["stat_name"])
            
            result["success"] = True
            result["home_stats"] = home_stats
            result["away_stats"] = away_stats
            result["stat_names"] = stat_names
            
            self._log(f"Successfully extracted {len(stat_names)} statistics", "SUCCESS")
            
        except Exception as e:
            self._log(f"Error extracting statistics: {e}", "ERROR")
            result["error"] = str(e)
            import traceback
            self._log(traceback.format_exc(), "DEBUG")
        
        return result

    def scrape_matches(
        self,
        url: str,
        season: str = None,
        max_rounds: int = 38,
        target_dates: Optional[List[str]] = None,
        sleep_s: float = 0.6,
        include_stats: bool = True,
    ) -> pd.DataFrame:
        """
        Scrape matches with complete information including statistics.
        
        Returns a DataFrame with all match data in separate columns.
        """
        
        df = self.scrape_gameweeks(
            url=url,
            season=season,
            max_rounds=max_rounds,
            target_dates=target_dates
        )

        if df is None or df.empty:
            return df

        if "link" not in df.columns:
            raise ValueError("Input dataframe must contain a 'link' column.")

        out_rows: List[Dict] = []

        for i, row in df.iterrows():
            link = str(row["link"])
            self._log(f"\n{'='*60}", "INFO")
            self._log(f"Match {i+1}/{len(df)}: {link}", "INFO")
            self._log(f"{'='*60}", "INFO")

            try:
                # Navigate to match page
                self.driver.get(self._abs_url(link))
                time.sleep(sleep_s)
                self._close_popups()

                # Extract basic info
                info = self._extract_match_header_info()
                
                out = row.to_dict()
                out.update(info)

                self._log(
                    f"Teams: {info['home_team_name']} vs {info['away_team_name']} @ {info['hour_of_the_match']}",
                    "SUCCESS",
                )

                # Extract statistics
                if include_stats:
                    # Navigate to Statistics tab
                    stat_nav = self.navigate_to_section(section_name="Statistics", wait_time=sleep_s)
                    
                    if stat_nav["success"]:
                        stats = self.extract_match_statistics(wait_time=sleep_s)
                        
                        if stats["success"]:
                            # Flatten all statistics into columns with prefixes
                            for stat_key, stat_value in stats["home_stats"].items():
                                out[f"home_{stat_key}"] = stat_value
                            
                            for stat_key, stat_value in stats["away_stats"].items():
                                out[f"away_{stat_key}"] = stat_value
                            
                            self._log(f"Stats extracted: {len(stats['home_stats'])} metrics", "SUCCESS")
                        else:
                            self._log("Failed to extract statistics", "WARNING")
                    else:
                        self._log("Could not navigate to Statistics tab", "WARNING")
                
                out_rows.append(out)
                
                # Small delay between matches
                time.sleep(sleep_s)

            except Exception as e:
                self._log(f"FAILED: {link}", "ERROR")
                self._log(f"Error: {e}", "ERROR")
                
                out = row.to_dict()
                out.update({
                    "home_team_name": "",
                    "away_team_name": "",
                    "hour_of_the_match": "",
                })
                out_rows.append(out)

        result_df = pd.DataFrame(out_rows)
        
        self._log(f"\n{'='*60}", "INFO")
        self._log(f"SCRAPING COMPLETE", "INFO")
        self._log(f"Total matches: {len(result_df)}", "INFO")
        self._log(f"Successful: {result_df['home_team_name'].notna().sum()}", "INFO")
        self._log(f"{'='*60}", "INFO")
        
        return result_df