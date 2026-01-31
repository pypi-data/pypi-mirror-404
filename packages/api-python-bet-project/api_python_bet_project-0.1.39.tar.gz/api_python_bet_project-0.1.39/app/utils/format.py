from typing import Tuple, Dict, Optional
import os
import unicodedata
import re

def _format_paths(
    templates: Dict[str, str],
    *,
    last_season: Tuple[str, int, int],
    country: str,
    competition: str,
    create_dirs: bool = True,
    base_dir: Optional[str] = None,
) -> Dict[str, str]:
    """
    Format path templates and optionally create parent directories (no files).
    """
    out: Dict[str, str] = {}
    for key, tpl in templates.items():
        try:
            path_str = tpl.format(
                last_season=last_season,
                country=country,
                competition=competition,
            )
        except Exception as exc:
            raise ValueError(
                f"Failed to format '{key}' with template '{tpl}': {exc}"
            ) from exc

        if base_dir:
            path_str = os.path.join(base_dir, path_str)

        if create_dirs:
            parent = os.path.dirname(path_str)
            if parent:
                os.makedirs(parent, exist_ok=True)

        out[key] = path_str
    return out


def _format_fbref(url_template: str, last_season: Tuple[str, int, int]) -> str:
    """
    Format a URL template by replacing {last_season[0|1|2]} placeholders.

    Args:
        url_template: URL with placeholders like {last_season[0]}, {last_season[1]}, {last_season[2]}
        last_season: Tuple (season_str, start_year, end_year)

    Returns:
        Formatted URL string

    Example:
        >>> _format_url("https://fbref.com/en/comps/12/{last_season[0]}/schedule/{last_season[1]}-{last_season[2]}", ("2017-2018", 2017, 2018))
        'https://fbref.com/en/comps/12/2017-2018/schedule/2017-2018'
    """
    if not url_template:
        return ""
    season_str, start_year, end_year = last_season
    return (
        url_template.replace("{last_season[0]}", str(season_str))
        .replace("{last_season[1]}", str(start_year))
        .replace("{last_season[2]}", str(end_year))
    )


def _format_fotmob(url_template: str, page: int) -> str:
    """
    Format FotMob URL with page number.

    Args:
        url_template: URL template with {page} placeholder
        page: Page number to insert

    Returns:
        Formatted URL with page number
    """
    return url_template.format(page=page)

def normalize_name(name: str) -> str:
    if not name:
        return ""
    s = str(name).strip()

    # 1) Remove accents using unicodedata
    # NFKD decompose: à -> a + ` (combining grave accent)
    s = unicodedata.normalize('NFKD', s)
    # Keep only ASCII characters (removes combining marks)
    s = s.encode('ascii', 'ignore').decode('ascii')

    # 2) Convert to lowercase
    s = s.lower()
    
    # 3) Replace spaces, hyphens, slashes, and apostrophes with underscores
    s = re.sub(r"[ \t/\-']+", "_", s)
    
    # 4) Collapse multiple underscores
    s = re.sub(r"_+", "_", s)
    
    # 5) Remove leading/trailing underscores
    s = s.strip("_")
    
    # 6) Normalize common abbreviations
    # Split by underscore, replace abbreviations, rejoin
    words = s.split('_')
    words = ['united' if word == 'utd' else word for word in words]
    s = '_'.join(words)

    return s