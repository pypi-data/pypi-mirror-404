"""
Transfermarkt scraper for player transfers.
"""

import requests
from bs4 import BeautifulSoup
import time
import re
import pandas as pd
from typing import Dict
from datetime import datetime
from utils.format import normalize_name


class TransfermarktScraper:
    """
    Scraper for Transfermarkt transfer data.
    
    Extracts player transfers (in/out) for each team in a competition.
    """
    
    def __init__(self, headers: Dict[str, str] = None):
        """
        Initialize scraper with optional custom headers.
        
        Args:
            headers: Custom headers for requests (optional)
        """
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_transfers(
        self, 
        url: str, 
        delay: float = 2.0,
        verbose: bool = False
    ) -> pd.DataFrame:
        """
        Scrape transfer data from Transfermarkt competition page.
        
        Args:
            url: Transfermarkt competition transfers URL
            delay: Delay between requests in seconds (default: 2.0)
            verbose: Print progress information
            
        Returns:
            DataFrame with columns: player_name, old_team, new_team, transfer_nature
        """
        
        if verbose:
            print(f"\n[TRANSFERS] ========== Scraping transfers ==========")
            print(f"[TRANSFERS] URL: {url}")
        
        # Make request
        try:
            time.sleep(delay)
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
        except Exception as e:
            print(f"[TRANSFERS] ERROR: Failed to fetch URL: {e}")
            raise
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all team boxes
        team_boxes = soup.find_all('div', class_='box')
        
        if not team_boxes:
            print(f"[TRANSFERS] WARNING: No team boxes found")
            return pd.DataFrame(columns=['player_name', 'old_team', 'new_team', 'transfer_nature'])
        
        if verbose:
            print(f"[TRANSFERS] Found {len(team_boxes)} team sections")
        
        # List to store all transfers
        all_transfers = []
        
        # Process each team box
        for box in team_boxes:
            # =====================================================================
            # EXTRACT TEAM NAME
            # =====================================================================
            team_name_raw = None
            
            # Look for h2 with class containing "content-box-headline"
            team_header = box.find('h2', class_=re.compile(r'content-box-headline'))
            
            if team_header:
                # Find the <a> tag with title attribute inside h2
                team_links = team_header.find_all('a', attrs={'title': True})
                
                for link in team_links:
                    title = link.get('title', '').strip()
                    # Skip if title is empty or contains "+Array"
                    if title and '+Array' not in title:
                        team_name_raw = title
                        break
                
                # Fallback: get text from first <a> tag
                if not team_name_raw:
                    first_link = team_header.find('a')
                    if first_link:
                        team_name_raw = first_link.text.strip()
            
            if not team_name_raw:
                if verbose:
                    print(f"[TRANSFERS] WARNING: Could not find team name in box, skipping")
                continue
            
            # Normalize team name
            team_name = normalize_name(team_name_raw)
            
            if not team_name:
                if verbose:
                    print(f"[TRANSFERS] WARNING: Team name is empty after normalization: '{team_name_raw}'")
                continue
            
            if verbose:
                print(f"\n[TRANSFERS] Processing team: {team_name_raw} → {team_name}")
            
            # Find tables inside responsive-table divs
            responsive_divs = box.find_all('div', class_='responsive-table')
            
            if not responsive_divs:
                if verbose:
                    print(f"[TRANSFERS]   No responsive-table divs found")
                continue
            
            for div in responsive_divs:
                table = div.find('table')
                if not table:
                    continue
                
                # Determine if it's In or Out table by checking header
                thead = table.find('thead')
                if not thead:
                    continue
                
                # Get all th elements
                headers_html = thead.find_all('th')
                
                # Check for "In" (arrivals) or "Out" (departures) in first column
                is_in_table = False
                is_out_table = False
                
                for th in headers_html:
                    th_text = th.text.strip()
                    th_class = ' '.join(th.get('class', []))
                    
                    # IN table has "In" in spieler-transfer-cell
                    if 'spieler-transfer-cell' in th_class and 'In' in th_text:
                        is_in_table = True
                        break
                    # OUT table has "Out" in spieler-transfer-cell
                    elif 'spieler-transfer-cell' in th_class and 'Out' in th_text:
                        is_out_table = True
                        break
                
                if not is_in_table and not is_out_table:
                    if verbose:
                        print(f"[TRANSFERS]   Skipping table (not In or Out)")
                    continue
                
                if verbose:
                    table_type = "IN" if is_in_table else "OUT"
                    print(f"[TRANSFERS]   Processing {table_type} table")
                
                # Process table rows - WITHOUT CLASS FILTER!
                tbody = table.find('tbody')
                if not tbody:
                    continue
                
                rows = tbody.find_all('tr')  # NO CLASS FILTER!
                
                if verbose:
                    print(f"[TRANSFERS]     Found {len(rows)} rows")
                
                for row in rows:
                    try:
                        transfer = self._extract_transfer_from_row(
                            row=row,
                            is_in_table=is_in_table,
                            current_team=team_name,
                            verbose=verbose
                        )
                        
                        if transfer:
                            all_transfers.append(transfer)
                    
                    except Exception as e:
                        if verbose:
                            print(f"[TRANSFERS]       ERROR parsing row: {e}")
                        continue
        
        # Create DataFrame
        df = pd.DataFrame(all_transfers)
        
        if verbose:
            print(f"\n[TRANSFERS] ========== Scraping complete ==========")
            print(f"[TRANSFERS] Total transfers: {len(df)}")
            print(f"[TRANSFERS] Unique players: {df['player_name'].nunique()}")
            
            # Show players with multiple transfers
            player_counts = df['player_name'].value_counts()
            multiple = player_counts[player_counts > 1]
            
            if len(multiple) > 0:
                print(f"[TRANSFERS] Players with multiple transfers: {len(multiple)}")
                print(f"\n[TRANSFERS] Examples:")
                for player in multiple.head(3).index:
                    player_transfers = df[df['player_name'] == player]
                    print(f"[TRANSFERS]   {player}: {len(player_transfers)} transfers")
                    for _, t in player_transfers.iterrows():
                        print(f"[TRANSFERS]     - {t['old_team']} → {t['new_team']} [{t['transfer_nature']}]")
        
        return df

    def _extract_transfer_from_row(
        self,
        row,
        is_in_table: bool,
        current_team: str,
        verbose: bool = False
    ) -> Dict[str, str]:
        """
        Extract transfer information from a table row.
        """
        
        # Get all cells
        cells = row.find_all('td')
        
        if len(cells) < 4:
            return None
        
        # =====================================================================
        # 1. EXTRACT PLAYER NAME
        # =====================================================================
        player_name_raw = None
        
        # Look in first cell for player name
        first_cell = cells[0]
        
        # Strategy 1: hide-for-small (desktop version)
        span_hide = first_cell.find('span', class_='hide-for-small')
        if span_hide:
            player_link = span_hide.find('a', attrs={'title': True})
            if player_link:
                player_name_raw = player_link.get('title', '').strip()
        
        # Strategy 2: show-for-small (mobile version)
        if not player_name_raw:
            span_show = first_cell.find('span', class_='show-for-small')
            if span_show:
                player_link = span_show.find('a', attrs={'title': True})
                if player_link:
                    player_name_raw = player_link.get('title', '').strip()
        
        # Strategy 3: any link in first cell
        if not player_name_raw:
            player_link = first_cell.find('a', attrs={'title': True})
            if player_link:
                player_name_raw = player_link.get('title', '').strip()
        
        if not player_name_raw:
            if verbose:
                print(f"[TRANSFERS]       WARNING: Could not find player name")
            return None
        
        # Normalize player name
        player_name = normalize_name(player_name_raw)
        
        # =====================================================================
        # 2. EXTRACT TEAM INFORMATION
        # =====================================================================
        
        team_raw = None
        
        # Look for cell with class "verein-flagge-transfer-cell"
        for cell in cells:
            cell_classes = cell.get('class', [])
            if 'verein-flagge-transfer-cell' in cell_classes:
                # Find link with title
                team_link = cell.find('a', attrs={'title': True})
                if team_link:
                    team_raw = team_link.get('title', '').strip()
                    break
        
        if not team_raw:
            if verbose:
                print(f"[TRANSFERS]       WARNING: Could not find team for {player_name_raw}")
            return None
        
        # =====================================================================
        # 3. EXTRACT TRANSFER NATURE (Fee/Type)
        # =====================================================================
        
        transfer_nature = None
        
        # Look for last cell (usually contains fee information)
        for cell in cells[-3:]:  # Check last 3 cells
            cell_classes = cell.get('class', [])
            if 'rechts' in cell_classes:
                # Get text content
                cell_text = cell.text.strip()
                
                if cell_text and cell_text != '-':
                    transfer_nature = cell_text
                    break
        
        # Normalize transfer nature
        if transfer_nature:
            transfer_nature = transfer_nature.strip()
            # Clean up common patterns
            transfer_nature = re.sub(r'\s+', ' ', transfer_nature)
        else:
            transfer_nature = 'unknown'
        
        # Determine old_team and new_team based on table type
        if is_in_table:
            # In table: player came FROM team_raw TO current_team
            old_team = normalize_name(team_raw)
            new_team = current_team
        else:
            # Out table: player LEFT current_team and JOINED team_raw
            old_team = current_team
            new_team = normalize_name(team_raw)
        
        transfer = {
            'player_name': player_name,
            'old_team': old_team,
            'new_team': new_team,
            'transfer_nature': transfer_nature
        }
        
        if verbose:
            print(f"[TRANSFERS]       ✓ {player_name_raw}: {old_team} → {new_team} [{transfer_nature}]")
        
        return transfer


def scrape_transfers_if_window_open(
    summer_url: str,
    winter_url: str,
    date: datetime,
    delay: float = 2.0, 
    verbose: bool = True
):
    """
    Scrape transfers only if transfer window is open on the given date.
    
    Args:
        url: Transfermarkt URL
        date: datetime object representing the scraping date
        delay: Delay between requests
        verbose: Print debug info
        
    Returns:
        Dictionary with transfers or None if window is closed
    """
    
    month = date.month
    day = date.day
    
    # Ventana verano: Agosto 1 - Septiembre 2
    is_summer = (month == 8) or (month == 9 and day <= 2)
    # Ventana invierno: Enero 1 - Febrero 3
    is_winter = (month == 1) or (month == 2 and day <= 3)
    
    if not is_summer and not is_winter:
        if verbose:
            print(f"⚠️  TRANSFER WINDOW CLOSED")
            print(f"   Date provided: {date.strftime('%Y-%m-%d')}")
            print(f"   Transfer windows:")
            print(f"     - Summer: August 1 - September 2")
            print(f"     - Winter: January 1 - February 3")
            print(f"\n   Scraping skipped.")
        return pd.DataFrame(columns=['player_name', 'old_team', 'new_team', 'transfer_nature'])
    
    # Determine which URL to use
    if is_summer:
        url = summer_url
        window_name = 'SUMMER'
    else:
        url = winter_url
        window_name = 'WINTER'
    
    if verbose:
        print(f"✅ TRANSFER WINDOW OPEN: {window_name}")
        print(f"   Date provided: {date.strftime('%Y-%m-%d')}")
        print(f"   Proceeding with scraping...\n")
    
    # Execute scraping
    scraper = TransfermarktScraper()
    transfers_df = scraper.scrape_transfers(
        url=url,
        delay=delay,
        verbose=verbose
    )
    
    return transfers_df

def _transfer_priority(transfer_nature: str) -> int:
    """
    Return priority for sorting repeated transfers.
    Lower number = earlier in the ordered chain.

    Priority:
      1) End of loan
      2) € / free transfer / ? / Without Club / Retired / Career break
      3) loan fee / loan transfer
      99) anything else (kept at the end)
    """
    s = "" if transfer_nature is None else str(transfer_nature).strip().lower()

    if "end of loan" in s:
        return 1

    if (
        "€" in str(transfer_nature)  # keep original to catch the symbol
        or "free transfer" in s
        or s == "?"
        or "without club" in s
        or "retired" in s
        or "career break" in s
    ):
        return 2

    if "loan fee" in s or "loan transfer" in s:
        return 3

    return 99


def dedupe_and_merge_repeated_players_transfers(csv: pd.DataFrame) -> pd.DataFrame:
    """
    1) Drop exact duplicate rows (all columns equal).
    2) For players with multiple remaining rows, sort them by transfer_nature priority,
       then replace them with a single merged row:
         - old_team = old_team of first row after sorting
         - new_team = new_team of last row after sorting

    Assumes columns: player_name, old_team, new_team, transfer_nature
    """
    required_cols = {"player_name", "old_team", "new_team", "transfer_nature"}
    missing = required_cols - set(csv.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # 1) Exact duplicates
    df = csv.drop_duplicates().copy()

    # Keep original order as stable tiebreaker
    df["_orig_order"] = range(len(df))
    df["_priority"] = df["transfer_nature"].apply(_transfer_priority)

    merged_rows = []

    for player_name, g in df.groupby("player_name", sort=False):
        if len(g) == 1:
            row = g.iloc[0].copy()
            merged_rows.append(row)
            continue

        g_sorted = g.sort_values(by=["_priority", "_orig_order"], ascending=True)

        first_row = g_sorted.iloc[0]
        last_row = g_sorted.iloc[-1]

        merged = first_row.copy()
        merged["old_team"] = first_row["old_team"]
        merged["new_team"] = last_row["new_team"]

        # Keep transfer_nature as something explicit (you can change this if you prefer)
        merged["transfer_nature"] = "MERGED_REPEATED_PLAYER"

        merged_rows.append(merged)

    out = pd.DataFrame(merged_rows).drop(columns=["_orig_order", "_priority"], errors="ignore")
    out = out.reset_index(drop=True)
    return out