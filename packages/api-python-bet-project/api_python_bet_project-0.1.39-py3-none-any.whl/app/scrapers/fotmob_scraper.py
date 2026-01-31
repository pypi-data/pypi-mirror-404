"""
FotMob Scraper - IMPROVED VERSION
Handles German team names and multiple variations
"""

import pandas as pd
from bs4 import BeautifulSoup
import re
import time
import traceback
import unicodedata
from typing import Dict, Optional, List
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# --- Constants & polite crawling settings ---
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) "
        "Gecko/20100101 Firefox/131.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "DNT": "1",
}
REQUEST_SLEEP_SECONDS = 6


class FotMobScraper:
    """Scraper for FotMob match links with improved German team name handling"""

    def __init__(self):
        """Initialize the scraper."""
        self.headers = REQUEST_HEADERS
        self.sleep_seconds = REQUEST_SLEEP_SECONDS

    def _normalize_team_name(self, team: str) -> str:
        """
        Normalize team name for comparison.
        Handles German characters, removes prefixes, and standardizes format.

        Args:
            team: Team name to normalize

        Returns:
            Normalized team name (lowercase, no special chars, no extra spaces)
        """
        normalized = team.strip().lower()
        
        # Replace underscores and hyphens with spaces
        normalized = normalized.replace("_", " ").replace("-", " ")
        
        # Replace German special characters with English equivalents
        normalized = normalized.replace("ü", "u").replace("ö", "o").replace("ä", "a").replace("ß", "ss")
        
        # Remove punctuation
        normalized = normalized.replace(".", "").replace(",", "")
        
        # Remove extra spaces
        normalized = " ".join(normalized.split())
        
        return normalized

    def _get_team_variations(self, team: str) -> List[str]:
        """
        Generate all possible variations of a team name for matching.
        
        Examples:
            "Bayern_Munich" → ["bayern munich", "bayern", "munich", "fc bayern", "fc bayern munich"]
            "VfB_Stuttgart" → ["vfb stuttgart", "stuttgart", "vfb"]
            "Borussia_Dortmund" → ["borussia dortmund", "dortmund", "bvb", "borussia"]
            "1._FC_Köln" → ["1 fc koln", "fc koln", "koln", "cologne"]
        
        Args:
            team: Team name
            
        Returns:
            List of all possible variations (normalized)
        """
        normalized = self._normalize_team_name(team)
        words = normalized.split()
        
        variations = set()
        
        # 1. Full name
        variations.add(normalized)
        
        # 2. Individual words (for partial matching)
        for word in words:
            if len(word) > 2:  # Skip very short words like "fc", "sv", "1"
                variations.add(word)
        
        # 3. Name without common prefixes/suffixes
        prefixes_to_remove = ["fc", "sv", "vfb", "tsv", "1", "bvb", "bsc", "rb", "fsv"]
        filtered_words = [w for w in words if w not in prefixes_to_remove]
        if filtered_words:
            variations.add(" ".join(filtered_words))
        
        # 4. With common prefixes (in case they're missing)
        core_name = " ".join(filtered_words) if filtered_words else normalized
        for prefix in ["fc", "vfb", "sv", "bvb"]:
            variations.add(f"{prefix} {core_name}")
        
        # 5. Special cases for known German teams
        special_mappings = {
            "munich": ["munchen", "bayern"],
            "munchen": ["munich", "bayern"],
            "bayern": ["munich", "munchen"],
            "cologne": ["koln"],
            "koln": ["cologne"],
            "monchengladbach": ["gladbach", "borussia monchengladbach"],
            "gladbach": ["monchengladbach"],
        }
        
        for word in words:
            if word in special_mappings:
                for mapped in special_mappings[word]:
                    variations.add(mapped)
                    if filtered_words:
                        # Replace the word with its mapping
                        temp_words = [mapped if w == word else w for w in filtered_words]
                        variations.add(" ".join(temp_words))
        
        return list(variations)

    def _teams_match(self, team1: str, team2: str) -> bool:
        """
        Check if two team names match, considering all variations.
        
        Args:
            team1: First team name (already normalized)
            team2: Second team name (already normalized)
            
        Returns:
            True if teams match
        """
        # Exact match
        if team1 == team2:
            return True
        
        # Get all variations for both teams
        variations1 = self._get_team_variations(team1)
        variations2 = self._get_team_variations(team2)
        
        # Check if any variation matches
        for v1 in variations1:
            for v2 in variations2:
                # Exact match
                if v1 == v2:
                    return True
                
                # Partial match (one contains the other)
                if v1 in v2 or v2 in v1:
                    # Make sure it's not too short to avoid false positives
                    shorter = min(v1, v2, key=len)
                    if len(shorter) >= 4:  # Minimum 4 chars for partial match
                        return True
        
        return False

    def parse_en_date_to_iso(self, date_str: str) -> Optional[str]:
        """
        Convert English date phrases into 'YYYY-MM-DD'. Returns None if it cannot parse.
        """
        if not date_str:
            return None

        s = date_str.strip()

        # 1) Normalize: remove commas, collapse spaces, lowercase
        s = s.replace(",", " ")
        s = re.sub(r"\s+", " ", s).strip().lower()

        # 2) Remove weekday if present (full or abbrev) at the start
        weekdays = {
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
            "mon", "tue", "tues", "wed", "thu", "thur", "thurs", "fri", "sat", "sun",
        }
        tokens = s.split()

        if tokens and tokens[0] in weekdays:
            tokens = tokens[1:]

        if not tokens:
            return None

        # 3) Month name mapping (long + short)
        months = {
            "january": "01", "february": "02", "march": "03", "april": "04",
            "may": "05", "june": "06", "july": "07", "august": "08",
            "september": "09", "october": "10", "november": "11", "december": "12",
            "jan": "01", "feb": "02", "mar": "03", "apr": "04",
            "may": "05", "jun": "06", "jul": "07", "aug": "08",
            "sep": "09", "sept": "09", "oct": "10", "nov": "11", "dec": "12",
        }

        # 4) Helper to strip ordinal suffixes: 1st, 2nd, 3rd, 4th...
        def _strip_ordinal(t: str) -> str:
            return re.sub(r"(?<=\d)(st|nd|rd|th)$", "", t)

        # Try Month-first pattern
        try:
            mi = next(i for i, t in enumerate(tokens) if t in months)
            if mi + 2 < len(tokens):
                day_tok = _strip_ordinal(tokens[mi + 1])
                year_tok = tokens[mi + 2]
                if day_tok.isdigit() and year_tok.isdigit() and int(year_tok) >= 1900:
                    m = months[tokens[mi]]
                    d = f"{int(day_tok):02d}"
                    y = year_tok
                    return f"{y}-{m}-{d}"
        except StopIteration:
            pass

        return None

    def _dates_match(self, date1: str, date2: str) -> bool:
        """
        Check if two dates match, handling different formats.
        
        Args:
            date1: Target date (can be "YYYY-MM-DD" or "YYYY-MM-DD HH:MM:SS")
            date2: FotMob date text (e.g., "Friday, August 18, 2017")
        
        Returns:
            True if dates match
        """
        # Normalize date1 to just YYYY-MM-DD (remove time if present)
        date1_normalized = str(date1).split()[0] if isinstance(date1, str) else str(date1)
        
        # Parse date2 from English format
        date2_parsed = self.parse_en_date_to_iso(date2)
        
        if date1_normalized == date2_parsed:
            return True
        return False

    def _fetch_page(self, page: int, fotmob_url: str) -> Optional[BeautifulSoup]:
        """Fetch a single page from FotMob using Selenium."""
        driver = None
        try:
            url = fotmob_url.format(page=page)

            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(url)

            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "section"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for sections")

            time.sleep(self.sleep_seconds)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            return soup

        except Exception as e:
            logger.error(f"Error fetching page {page}: {e}")
            logger.error(traceback.format_exc())
            return None

        finally:
            if driver:
                driver.quit()

    def _extract_date_sections(
        self, soup: BeautifulSoup, target_dates: list, page_num: int = 0
    ) -> Dict[str, List[Dict]]:
        """Extract all match links for specific dates from a page."""
        sections_by_date = {}

        all_sections = soup.find_all(
            "section", class_=lambda x: x and "LeagueMatchesSection" in str(x)
        )
        
        print(f"         🔍 Found {len(all_sections)} LeagueMatchesSection sections on page")

        for idx, section in enumerate(all_sections):
            header = section.find("h3", class_=lambda x: x and "Header" in str(x))

            if not header:
                if idx < 3 and page_num == 0:  # Debug first page
                    print(f"         ⚠️  Section {idx}: No header found")
                continue

            date_text = header.get_text(strip=True)
            
            if idx < 3 and page_num == 0:  # Debug first page
                print(f"         📅 Section {idx} header text: '{date_text}'")

            matched_date = None
            for target_date in target_dates:
                if self._dates_match(target_date, date_text):
                    # Normalize the matched date to YYYY-MM-DD format
                    matched_date = str(target_date).split()[0] if isinstance(target_date, str) else str(target_date).split()[0]
                    if page_num == 0:
                        print(f"            ✅ MATCHED with target date: {matched_date}")
                    break

            if not matched_date:
                if idx < 3 and page_num == 0:
                    # Show why it didn't match
                    parsed = self.parse_en_date_to_iso(date_text)
                    print(f"            ❌ No match. Parsed to: {parsed}")
                    print(f"            Looking for: {[str(d).split()[0] for d in target_dates]}")
                continue

            match_links = section.find_all(
                "a", class_=lambda x: x and "MatchWrapper" in str(x)
            )
            
            if page_num == 0:
                print(f"            Found {len(match_links)} matches for this date")

            for link in match_links:
                match_url = link.get("href")
                if not match_url:
                    continue

                team_spans = link.find_all(
                    "span", class_=lambda x: x and "TeamName" in str(x)
                )

                if len(team_spans) >= 2:
                    home_team_text = team_spans[0].get_text(strip=True)
                    away_team_text = team_spans[1].get_text(strip=True)

                    if match_url.startswith("/"):
                        match_url = f"https://www.fotmob.com{match_url}"

                    match_info = {
                        "date": matched_date,
                        "home_team": home_team_text,
                        "away_team": away_team_text,
                        "home_team_norm": self._normalize_team_name(home_team_text),
                        "away_team_norm": self._normalize_team_name(away_team_text),
                        "url": match_url,
                    }

                    if matched_date not in sections_by_date:
                        sections_by_date[matched_date] = []
                    sections_by_date[matched_date].append(match_info)

        return sections_by_date

    def find_matches(
        self, target_matches: pd.DataFrame, fotmob_url: str, max_pages: int = 60
    ) -> pd.DataFrame:
        """Find match URLs for specific team matchups and dates."""
        print("=" * 80)
        print("🔍 STARTING find_matches() - IMPROVED VERSION")
        print("=" * 80)
        print(f"📊 Target matches input: {len(target_matches)} rows")
        print(f"🔗 FotMob URL: {fotmob_url}")
        print(f"📄 Max pages to scrape: {max_pages}")

        # Normalize target matches
        print("\n🔧 Normalizing target matches...")
        target_matches = target_matches.copy()
        target_matches["home_team_norm"] = target_matches["home_team"].apply(
            self._normalize_team_name
        )
        target_matches["away_team_norm"] = target_matches["away_team"].apply(
            self._normalize_team_name
        )
        target_matches["url"] = None
        target_matches["found"] = False
        print("   ✓ Normalization complete")
        
        # Print some examples
        print("\n   📝 First 3 normalized examples:")
        for idx in range(min(3, len(target_matches))):
            row = target_matches.iloc[idx]
            print(f"      {row['home_team']} → {row['home_team_norm']}")
            print(f"      {row['away_team']} → {row['away_team_norm']}")

        # STEP 1: Extract all unique dates
        print("\n📅 STEP 1: Extracting unique dates...")
        unique_dates_raw = target_matches["date"].unique()
        # Normalize dates to YYYY-MM-DD format (remove time if present)
        unique_dates = set()
        for date in unique_dates_raw:
            date_str = str(date).split()[0] if isinstance(date, str) else str(date).split()[0]
            unique_dates.add(date_str)
        
        print(f"   ✓ Found {len(unique_dates)} unique dates:")
        for date in sorted(unique_dates):
            print(f"      - {date}")

        # STEP 2: Scrape pages until all dates are found
        print(f"\n🌐 STEP 2: Scraping pages for dates...")
        sections_by_date = {}
        dates_found = set()

        for page in range(max_pages):
            print(f"\n   📄 Page {page + 1}/{max_pages}")
            print(f"      Dates found so far: {len(dates_found)}/{len(unique_dates)}")
            
            if dates_found:
                print(f"      Found dates: {sorted(dates_found)}")
            
            print(f"      Fetching page {page}...")
            soup = self._fetch_page(page, fotmob_url)

            if soup is None:
                print(f"      ❌ Failed to fetch page {page} - stopping")
                break
            
            print(f"      ✓ Page fetched successfully")

            print(f"      Extracting date sections...")
            page_sections = self._extract_date_sections(soup, unique_dates, page_num=page)
            print(f"      ✓ Found {len(page_sections)} date sections in this page")

            for date, matches in page_sections.items():
                if date not in sections_by_date:
                    sections_by_date[date] = []
                    print(f"         🆕 New date found: {date} ({len(matches)} matches)")
                else:
                    print(f"         ➕ Adding to date {date} (+{len(matches)} matches)")
                
                sections_by_date[date].extend(matches)
                dates_found.add(date)

            if dates_found == unique_dates:
                print(f"\n   ✅ All {len(unique_dates)} dates found! Stopping early at page {page + 1}")
                break

            if page < max_pages - 1:
                print(f"      😴 Sleeping {self.sleep_seconds}s before next page...")
                time.sleep(self.sleep_seconds)

        print(f"\n   📈 Scraping summary:")
        print(f"      Pages scraped: {page + 1}")
        print(f"      Dates found: {len(dates_found)}/{len(unique_dates)}")
        print(f"      Total match sections collected: {sum(len(v) for v in sections_by_date.values())}")
        
        if dates_found != unique_dates:
            missing_dates = unique_dates - dates_found
            print(f"      ⚠️  Missing dates: {sorted(missing_dates)}")

        # STEP 3: Match target matches with found matches
        print(f"\n🎯 STEP 3: Matching target matches with found matches (IMPROVED MATCHING)...")
        
        matches_processed = 0
        matches_found = 0
        
        for idx, target in target_matches.iterrows():
            matches_processed += 1
            
            if matches_processed % 10 == 0:
                print(f"\n   📍 Progress: {matches_processed}/{len(target_matches)} matches processed")
                print(f"      Matches found: {matches_found}")
            
            if target["found"]:
                continue

            # Normalize date to YYYY-MM-DD format
            target_date_raw = target["date"]
            target_date = str(target_date_raw).split()[0] if isinstance(target_date_raw, str) else str(target_date_raw).split()[0]
            target_home = target["home_team_norm"]
            target_away = target["away_team_norm"]

            if matches_processed <= 5:
                print(f"\n   🔎 Match {idx}:")
                print(f"      Date: {target_date}")
                print(f"      Home: {target['home_team']} → {target_home}")
                print(f"      Away: {target['away_team']} → {target_away}")
                # Show variations
                home_vars = self._get_team_variations(target['home_team'])
                away_vars = self._get_team_variations(target['away_team'])
                print(f"      Home variations: {home_vars[:5]}...")
                print(f"      Away variations: {away_vars[:5]}...")

            date_matches = sections_by_date.get(target_date, [])

            if not date_matches:
                if matches_processed <= 5:
                    print(f"      ❌ No matches found for date {target_date}")
                continue

            if matches_processed <= 5:
                print(f"      ℹ️  Found {len(date_matches)} matches for this date")
                # Show what teams are available
                print(f"      Available matches:")
                for dm in date_matches[:3]:
                    print(f"         - {dm['home_team']} vs {dm['away_team']}")

            match_found = self._find_match_in_list(
                date_matches,
                target_home,
                target_away,
                target["home_team"],
                target["away_team"],
            )

            if match_found:
                target_matches.at[idx, "url"] = match_found["url"]
                target_matches.at[idx, "found"] = True
                matches_found += 1
                
                if matches_processed <= 5:
                    print(f"      ✅ Match found!")
                    print(f"         FotMob: {match_found['home_team']} vs {match_found['away_team']}")
                    print(f"         URL: {match_found['url']}")
            else:
                if matches_processed <= 5:
                    print(f"      ❌ Match not found in available matches")

        # Final report
        print(f"\n{'=' * 80}")
        print(f"📊 FINAL RESULTS:")
        print(f"{'=' * 80}")
        found_count = target_matches["found"].sum()
        print(f"   Matches requested: {len(target_matches)}")
        print(f"   Matches found: {found_count}")
        print(f"   Success rate: {found_count / len(target_matches) * 100:.1f}%")
        
        not_found = target_matches[~target_matches["found"]]
        if not not_found.empty:
            print(f"\n   ⚠️  Matches not found ({len(not_found)}):")
            for idx, row in not_found.head(10).iterrows():
                print(f"      - {row['date']}: {row['home_team']} vs {row['away_team']}")
            if len(not_found) > 10:
                print(f"      ... and {len(not_found) - 10} more")
        
        print("=" * 80)

        return target_matches

    def _find_match_in_list(
        self,
        date_matches: List[Dict],
        target_home_norm: str,
        target_away_norm: str,
    ) -> Optional[Dict]:
        """Find a specific match in a list using improved team matching."""
        # Try normal order first (home vs away)
        for match in date_matches:
            match_home = match["home_team_norm"]
            match_away = match["away_team_norm"]

            if self._teams_match(match_home, target_home_norm) and self._teams_match(
                match_away, target_away_norm
            ):
                return match

        # Try reversed order (away vs home)
        for match in date_matches:
            match_home = match["home_team_norm"]
            match_away = match["away_team_norm"]

            if self._teams_match(match_home, target_away_norm) and self._teams_match(
                match_away, target_home_norm
            ):
                return match

        return None

    def scrape_injuries_from_match(self, match_url: str) -> Dict[str, List[str]]:
        """Scrape injured players from a FotMob match page."""
        driver = None
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")

            driver = webdriver.Chrome(options=chrome_options)
            driver.get(match_url)

            time.sleep(self.sleep_seconds)

            for _ in range(3):
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")

            all_4pi1g3_sections = soup.find_all(
                "section",
                class_=lambda x: x and "4pi1g3" in str(x) and "BenchesContainer" in str(x),
            )

            if len(all_4pi1g3_sections) < 3:
                return {"home_injuries": [], "away_injuries": []}

            injuries_container = all_4pi1g3_sections[-1]

            bench_uls = injuries_container.find_all(
                "ul", class_=lambda x: x and "BenchContainer" in str(x)
            )

            if len(bench_uls) < 2:
                return {"home_injuries": [], "away_injuries": []}

            home_injuries = []
            away_injuries = []

            for idx, ul in enumerate(bench_uls[:2]):
                team_injuries = []

                player_links = ul.find_all(
                    "a", href=lambda x: x and "/players/" in str(x)
                )

                for player_link in player_links:
                    href = player_link.get("href", "")

                    if "/players/" in href:
                        url_parts = href.rstrip("/").split("/")
                        player_slug = url_parts[-1]
                        player_name = player_slug.replace("-", "_")

                        if player_name not in team_injuries:
                            team_injuries.append(player_name)

                if idx == 0:
                    home_injuries = team_injuries
                elif idx == 1:
                    away_injuries = team_injuries

            return {"home_injuries": home_injuries, "away_injuries": away_injuries}

        except Exception as e:
            return {"home_injuries": [], "away_injuries": []}

        finally:
            if driver:
                driver.quit()

    def _slugify_name(self, name: str) -> str:
        s = str(name or "").strip().lower()
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("utf-8")
        s = re.sub(r"[^a-z0-9]+", "_", s)
        return s.strip("_")

    def scrape_all_injuries(
        self, target_matches: pd.DataFrame, fotmob_url: str
    ) -> list[str]:
        """Scrape injuries for all matches and return a unique list of injured player slugs."""
        print("=" * 80)
        print("🏥 STARTING scrape_all_injuries()")
        print("=" * 80)
        print(f"📊 Target matches input: {len(target_matches)} rows")
        print(f"🔗 FotMob URL: {fotmob_url}")
        
        print("\n🔍 Finding matches...")
        matches_df = self.find_matches(target_matches, fotmob_url)
        print(f"✓ Found {len(matches_df)} matches to process")
        
        if matches_df.empty:
            print("⚠️  No matches found - returning empty list")
            return []

        injured_all: list[str] = []
        
        print(f"\n🔄 Processing {len(matches_df)} matches...")
        
        for idx, row in matches_df.iterrows():
            if idx % 10 == 0:
                print(f"\n   📍 Progress: {idx}/{len(matches_df)} matches processed")
                print(f"   💉 Total injuries found so far: {len(injured_all)}")
            
            match_url = row.get("url")
            if pd.isna(match_url) or not match_url:
                if idx < 5:
                    print(f"   ⚠️  Match {idx}: No URL found, skipping")
                continue
            
            if idx < 5:
                print(f"\n   🔎 Match {idx}: {match_url}")
            
            try:
                if idx < 5:
                    print(f"      Scraping injuries...")
                injuries_data = self.scrape_injuries_from_match(match_url)
                
                if idx < 5:
                    print(f"      ✓ Scraped successfully")
                    print(f"      Home injuries: {len(injuries_data.get('home_injuries', []))}")
                    print(f"      Away injuries: {len(injuries_data.get('away_injuries', []))}")
                
            except Exception as e:
                if idx < 5:
                    print(f"      ❌ Error scraping: {str(e)[:100]}")
                continue

            injuries_count_before = len(injured_all)
            
            for key in ("home_injuries", "away_injuries"):
                players = injuries_data.get(key) or []
                for p in players:
                    if not p:
                        continue
                    slug = self._slugify_name(p)
                    injured_all.append(slug)
                    
                    if idx < 5:
                        print(f"      Added injury: {p} → {slug}")
            
            injuries_added = len(injured_all) - injuries_count_before
            if idx < 5 and injuries_added > 0:
                print(f"      ✓ Added {injuries_added} injuries from this match")

            if idx < len(matches_df) - 1:
                if idx < 5:
                    print(f"      😴 Sleeping {self.sleep_seconds}s...")
                time.sleep(self.sleep_seconds)

        print(f"\n📈 Scraping complete!")
        print(f"   Total injuries collected: {len(injured_all)}")
        print(f"   Unique injuries (before dedup): {len(set(injured_all))}")
        
        print("\n🔧 Removing duplicates...")
        seen = set()
        injured_unique: list[str] = []
        for x in injured_all:
            if x not in seen:
                seen.add(x)
                injured_unique.append(x)

        print(f"✅ Final unique injured players: {len(injured_unique)}")
        
        if len(injured_unique) > 0 and len(injured_unique) <= 10:
            print(f"   Players: {injured_unique}")
        elif len(injured_unique) > 10:
            print(f"   First 10: {injured_unique[:10]}")
            print(f"   ... and {len(injured_unique) - 10} more")
        
        print("=" * 80)
        
        return injured_unique