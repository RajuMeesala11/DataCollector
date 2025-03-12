import os
import json
import openai
from time import sleep

# Set your OpenAI API key (or set it via your environment variable)

def extract_fields_from_json(facility_json_str: str) -> dict:
    """
    Sends the entire facility JSON (as a string) to GPT-3.5-turbo for extraction.
    Returns a dict with standardized fields.
    """
    prompt = f"""
You are an AI assistant that extracts specific standardized information from a facility's JSON data.
Below is the facility data delimited by triple backticks:
{facility_json_str}
Extract and return the following fields as a valid JSON object (use empty string if not found):
- Name
- Street Address
- City
- State
- Zip Code
- Provider
- Country(US, UK, etc.)
- State
- Whitespace(Total building area in Sq. Ft.)
- Area(Building area in Sq. Ft.)
- Year Built(YYYY)
- Power(in KW)
- Scale(Hyperscale, Enterprise, etc.)
- Certifications
- URL

Output format (strict JSON):
{{
  "Name": "",
  "Provider": "",
  "StreetAddress": "",
  "City": "",
  "ZipCode": "",
  "State": "",
  "Country": "",
  "Whitespace": "",
  "Area": "",
  "YearBuilt": "",
  "Power": "",
  "Scale": "",
  "Certifications": "",
  "URL": ""
}}
Do not include any extra keys.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful AI that extracts structured information from JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=300
        )
        content = response.choices[0].message.content.strip()
         # If response is empty, retry
        extracted_data = json.loads(content)
    except Exception as e:
        print("Error during extraction:", e)
        extracted_data = {
            "Name": "",
            "Provider": "",
            "StreetAddress": "",
            "City": "",
            "ZipCode": "",
            "State": "",
            "Country": "",
            "Whitespace": "",
            "Area": "",
            "YearBuilt": "",
            "Power": "",
            "Scale": "",
            "Certifications": "",
            "URL": ""
        }
    return extracted_data

def load_progress(output_file: str):
    """Load already processed records if the output file exists."""
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            progress = json.load(f)
    else:
        progress = []
    return progress

def save_progress(output_file: str, data: list):
    """Save the progress (list of processed facilities) to the output file."""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def process_hawk(input_file: str, output_file: str):
    """
    Processes datacenterhawk data.
    The structure: 
    {
      "markets": {
         "Northern Virginia": {
             "name": "Northern Virginia",
             "link": "...",
             "facilities": {
                 "facility_1": { ... },
                 "facility_2": { ... }
             }
         },
         ...
      }
    }
    """
    progress = load_progress(output_file)
    processed_keys = {record["unique_key"] for record in progress if record.get("unique_key")}
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    markets = data.get("markets", {})
    for market_key, market_data in markets.items():
        market_name = market_data.get("name", market_key)
        facilities = market_data.get("facilities", {})
        for fac_key, fac_data in facilities.items():
            unique_key = f"{market_name}_{fac_key}"
            if unique_key in processed_keys:
                continue  # Skip if already processed
            # Combine market context with facility data
            facility_combined = {
                "market": market_name,
                **fac_data
            }
            facility_json_str = json.dumps(facility_combined, ensure_ascii=False)
            extracted = extract_fields_from_json(facility_json_str)
            result = {
                "unique_key": unique_key,
                "source": "datacenterhawk",
                "Name": extracted.get("Name", ""),
                "Provider": extracted.get("Provider", ""),
                "StreetAddress": extracted.get("StreetAddress", ""),
                "City": extracted.get("City", ""),
                "ZipCode": extracted.get("ZipCode", ""),
                "State": extracted.get("State", ""),
                "Country": extracted.get("Country", ""),
                "Whitespace": extracted.get("Whitespace", ""),
                "Area": extracted.get("Area", ""),
                "YearBuilt": extracted.get("YearBuilt", ""),
                "Power": extracted.get("Power", ""),
                "Scale": extracted.get("Scale", ""),
                "Certifications": extracted.get("Certifications", ""),
                "URL": extracted.get("URL", "") or fac_data.get("url", "")
            }
            progress.append(result)
            processed_keys.add(unique_key)
            print(f"Processed {unique_key}")
            sleep(0.5)
            save_progress(output_file, progress)
    save_progress(output_file, progress)
    print(f"Finished processing datacenterhawk. Total records: {len(progress)}")

def process_centers(input_file: str, output_file: str):
    """
    Processes datacenters.com data.
    The structure: 
    {
      "facility_id": {
          "Name": "...",
          "Address": "...",
          "Description1": "...",
          "Description2": "...",
          "TableInfo": { ... },
          "Url": "..."
      },
      ...
    }
    """
    progress = load_progress(output_file)
    processed_keys = {record["unique_key"] for record in progress if record.get("unique_key")}
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for facility_id, facility_data in data.items():
        unique_key = facility_id  # Unique identifier for this source
        if unique_key in processed_keys:
            continue
        combined_data = facility_data.copy()
        desc1 = facility_data.get("Description1", "")
        desc2 = facility_data.get("Description2", "")
        combined_data["combinedDescription"] = desc1 + "\n" + desc2
        facility_json_str = json.dumps(combined_data, ensure_ascii=False)
        extracted = extract_fields_from_json(facility_json_str)
        result = {
            "unique_key": unique_key,
            "source": "datacenters.com",
            "Name": extracted.get("Name", ""),
            "Provider": extracted.get("Provider", ""),
            "StreetAddress": extracted.get("StreetAddress", ""),
            "City": extracted.get("City", ""),
            "ZipCode": extracted.get("ZipCode", ""),
            "State": extracted.get("State", ""),
            "Country": extracted.get("Country", ""),
            "Whitespace": extracted.get("Whitespace", ""),
            "Area": extracted.get("Area", ""),
            "YearBuilt": extracted.get("YearBuilt", ""),
            "Power": extracted.get("Power", ""),
            "Scale": extracted.get("Scale", ""),
            "Certifications": extracted.get("Certifications", ""),
            "URL": extracted.get("URL", "") or facility_data.get("Url", "")
        }
        progress.append(result)
        processed_keys.add(unique_key)
        print(f"Processed {unique_key}")
        sleep(0.5)
        save_progress(output_file, progress)
    save_progress(output_file, progress)
    print(f"Finished processing datacenters.com. Total records: {len(progress)}")

def process_datacentermap(input_file: str, output_file: str):
    """
    Processes datacentermap data.
    The structure: 
    {
      "Virginia": {
         "count": "...",
         "details": [
             {
                 "name": "Ashburn",
                 "url": "...",
                 "count": "...",
                 "addresses": [
                     {
                         "url": "...",
                         "name": "...",
                         "address1": "...",
                         "address2": "...",
                         "address3": "...",
                         "overviewHTML": "...",
                         "specsHtml": "..."
                     },
                     ...
                 ]
             },
             ...
         ]
      },
      ...
    }
    For each state, for each detail (e.g., city), and for each address, we combine context.
    """
    progress = load_progress(output_file)
    processed_keys = {record["unique_key"] for record in progress if record.get("unique_key")}
    
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for state, state_data in data.items():
        details = state_data.get("details", [])
        for detail in details:
            city_name = detail.get("name", "")
            addresses = detail.get("addresses", [])
            for address in addresses:
                addr_url = address.get("url", "")
                unique_key = f"{state}_{city_name}_{addr_url}"
                if unique_key in processed_keys:
                    continue
                combined_data = {
                    "state": state,
                    "city": city_name,
                    "detail_url": detail.get("url", ""),
                    **address
                }
                facility_json_str = json.dumps(combined_data, ensure_ascii=False)
                extracted = extract_fields_from_json(facility_json_str)
                result = {
                    "unique_key": unique_key,
                    "source": "datacentermap",
                    "Name": extracted.get("Name", ""),
                    "Provider": extracted.get("Provider", ""),
                    "StreetAddress": extracted.get("StreetAddress", ""),
                    "City": extracted.get("City", ""),
                    "ZipCode": extracted.get("ZipCode", ""),
                    "State": extracted.get("State", ""),
                    "Country": extracted.get("Country", ""),
                    "Whitespace": extracted.get("Whitespace", ""),
                    "Area": extracted.get("Area", ""),
                    "YearBuilt": extracted.get("YearBuilt", ""),
                    "Power": extracted.get("Power", ""),
                    "Scale": extracted.get("Scale", ""),
                    "Certifications": extracted.get("Certifications", ""),
                    "URL": extracted.get("URL", "") or address.get("url", "")
                }
                progress.append(result)
                processed_keys.add(unique_key)
                print(f"Processed {unique_key}")
                sleep(0.5)
                save_progress(output_file, progress)
    save_progress(output_file, progress)
    print(f"Finished processing datacentermap. Total records: {len(progress)}")

def main():
    # Update file paths as necessary
    process_datacentermap("map_final.json", "map_extracted.json")
    process_hawk("hawk_final.json", "hawk_extracted.json")
    process_centers("centers_final.json", "centers_extracted.json")
    

if __name__ == "__main__":
    main()