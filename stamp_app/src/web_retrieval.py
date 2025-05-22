import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, quote_plus

# This file will handle fetching stamp information from online resources.
# It will include functions for querying web APIs or scraping websites
# to gather details about identified stamps.

def fetch_stamp_information(
    stamp_image_path: str, search_keywords: str, target_url: str
) -> list[dict]:
    """
    Fetches stamp information from a target URL based on search keywords.

    This function sends a search query to the target_url, parses the HTML
    response, and attempts to extract titles, URLs, and snippets from the
    search results.

    Args:
        stamp_image_path: Path to the individual detected stamp image.
                          (Currently a placeholder, not used for image analysis).
        search_keywords: Keywords to use for the search query.
        target_url: The base URL of the website to search. The function
                    will append a search query parameter, typically '?q='.

    Returns:
        A list of dictionaries, where each dictionary contains:
        - 'title': Title of the search result.
        - 'url': Absolute URL of the search result.
        - 'snippet': A short description or snippet.
        - 'estimated_price_range': Placeholder, defaults to "Not found".
        - 'country': Placeholder, defaults to "Not found".
        - 'history_notes': Placeholder, defaults to "Not found".
        Returns an empty list if no results are found or an error occurs.
    """
    results = []
    if not search_keywords or not target_url:
        return results

    # Construct the search URL. This is a common pattern for many search engines.
    # We use quote_plus to URL-encode the search keywords.
    try:
        # Basic check to see if target_url already contains query params
        if "?" in target_url:
            search_url = f"{target_url}&q={quote_plus(search_keywords)}"
        else:
            search_url = f"{target_url}?q={quote_plus(search_keywords)}"

        print(f"Fetching information from: {search_url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {search_url}: {e}")
        return results
    except Exception as e:
        print(f"An unexpected error occurred during request: {e}")
        return results

    try:
        soup = BeautifulSoup(response.content, "html.parser")

        # --- Generic Google Search Result Parsing Logic ---
        # This logic is highly specific to Google's current HTML structure
        # and is prone to break if Google changes its layout.
        # For a specific stamp catalogue, this parsing logic would be different.

        # Google search results are often within <div> elements with class 'g' or similar.
        # This is a common, but fragile, selector.
        # We'll look for common patterns like an <h3> for the title and a <div> for the snippet.
        
        # Google uses <div>s with class 'tF2Cxc' or 'g' for organic results.
        # Let's try to find a common container for each result.
        # We'll look for <a> tags with <h3> inside them for titles, then navigate for snippets.
        
        # Update: Google's structure (as of late 2023/early 2024) often uses:
        # A div that contains an <a> tag, and within that <a> tag is an <h3> for the title.
        # The snippet is often in a sibling or nearby div.

        for item in soup.find_all("div", class_=["g", "Gx5Zad", "hlcw0c", "tF2Cxc"]): # Common Google result containers
            title_element = item.find("h3")
            link_element = item.find("a")
            
            title = title_element.get_text() if title_element else "No title found"
            url = link_element["href"] if link_element and link_element.has_attr("href") else "No URL found"

            # Make URL absolute if it's relative
            if url.startswith("/"):
                url = urljoin(target_url, url)
            
            # Snippet extraction is tricky. Google uses different structures.
            # Trying a few common patterns for snippets.
            snippet_element = item.find("div", class_=["VwiC3b", "s3v9rd", "BNeawe", "UPmit AP7Wnd"])
            snippet = snippet_element.get_text(separator=" ", strip=True) if snippet_element else "No snippet found."
            
            # Fallback if specific snippet classes are not found
            if snippet == "No snippet found.":
                # Look for a div that might contain the snippet text directly within the item
                # This is very generic.
                text_blocks = item.find_all(string=True, recursive=True)
                full_text = ' '.join(filter(None, [t.strip() for t in text_blocks]))
                # Try to get a reasonable length snippet, avoiding menu items etc.
                # This is a heuristic.
                if title in full_text and len(full_text) > len(title):
                     potential_snippet = full_text[full_text.find(title):].split("\n")[0]
                     if len(potential_snippet) > 150: # Limit snippet length
                         potential_snippet = potential_snippet[:150] + "..."
                     if len(potential_snippet) > 20 and not potential_snippet.startswith("http"): # Basic filter
                        snippet = potential_snippet

            if title != "No title found" and url != "No URL found":
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "estimated_price_range": "Not found", # Placeholder
                    "country": "Not found",               # Placeholder
                    "history_notes": "Not found",         # Placeholder
                })
            
            if len(results) >= 5: # Limit to first 5 relevant results
                break
        
        if not results and soup.title: # If no specific results, maybe provide page title
            print(f"Could not parse specific search results, page title: {soup.title.string}")


    except Exception as e:
        print(f"Error parsing HTML content: {e}")
        # results list will remain empty or partially filled

    return results


def main_test():
    """
    Tests the fetch_stamp_information function with sample data.
    """
    print("Testing fetch_stamp_information...")

    # Dummy path, not used by the current version of the function for analysis
    dummy_image_path = "/path/to/some/stamp_image.png"

    # Keywords for search
    # search_keywords = "Canada Queen Elizabeth II 5 cent stamp"
    search_keywords = "rare postage stamps USA"

    # Target URL for search (Google Search)
    # Using Google as a generic example. Scraping Google can be unreliable
    # and is against their ToS for automated queries if not done carefully.
    # A specific stamp catalogue or API would be much better.
    target_url = "https://www.google.com/search"
    # Alternative for testing: a site that might be friendlier to scraping, if available
    # target_url = "https://www.example.com/search" # Replace with a real, scrapable site if possible

    print(f"\nSearching for: '{search_keywords}' on {target_url}")
    fetched_info = fetch_stamp_information(dummy_image_path, search_keywords, target_url)

    if fetched_info:
        print("\n--- Fetched Information ---")
        for i, info in enumerate(fetched_info):
            print(f"\nResult {i+1}:")
            print(f"  Title: {info['title']}")
            print(f"  URL: {info['url']}")
            print(f"  Snippet: {info['snippet']}")
            print(f"  Price Range: {info['estimated_price_range']}")
            print(f"  Country: {info['country']}")
            print(f"  History: {info['history_notes']}")
    else:
        print("\nNo information fetched or an error occurred.")

    # Example with a more specific (but still hypothetical) query
    search_keywords_specific = "Penny Black value"
    print(f"\nSearching for: '{search_keywords_specific}' on {target_url}")
    fetched_info_specific = fetch_stamp_information(dummy_image_path, search_keywords_specific, target_url)

    if fetched_info_specific:
        print("\n--- Fetched Information (Specific) ---")
        for i, info in enumerate(fetched_info_specific):
            print(f"\nResult {i+1}:")
            print(f"  Title: {info['title']}")
            print(f"  URL: {info['url']}")
            print(f"  Snippet: {info['snippet']}")
    else:
        print("\nNo information fetched for the specific query or an error occurred.")


if __name__ == "__main__":
    main_test()
