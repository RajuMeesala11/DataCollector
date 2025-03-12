import os
import json
import time
import openai
from time import sleep

# Set your OpenAI API key

# File Paths
INPUT_FILE = "centers_final.json"
OUTPUT_FILE = "centers_extracted.json"
FAILED_CASES_FILE = "failed_cases.json"

# Limit for description length to prevent exceeding API token limits
MAX_DESC_LENGTH = 1500  

def clean_text(text):
    """Removes excessive newlines, trims spaces, and truncates long text."""
    if not text:
        return ""
    return " ".join(text.split())[:MAX_DESC_LENGTH]

def extract_fields_from_json(facility_json_str: str, retries: int = 2) -> dict:
    """
    Extracts structured information from facility JSON using OpenAI API.
    Retries if OpenAI fails to return valid data.
    """
    facility_data = json.loads(facility_json_str)

    # ✅ Normalize descriptions before sending
    description_combined = f"{facility_data.get('Description1', '')} {facility_data.get('Description2', '')}"
    facility_data["Description"] = clean_text(description_combined)

    facility_json_str = json.dumps(facility_data, ensure_ascii=False)

    prompt = f"""
You are an AI assistant extracting structured information from facility JSON data.
Below is the facility data delimited by triple backticks:
{facility_json_str}
Extract and return the following fields as a valid JSON object (use empty string if not found):
- Name
- Street Address
- City
- State (2-letter US state code)
- Zip Code
- Provider (Company operating the facility)
- Country (US, UK, etc.)
- Whitespace (Total building area in Sq. Ft.)
- Area (Building area in Sq. Ft.)
- Year Built (YYYY)
- Power (in kW)
- Scale (Hyperscale, Enterprise, etc.)
- Certifications (List of certifications, e.g., SOC 2, HIPAA)
- URL

Output format (strict JSON):
{{
  "Name": "",
  "Street Address": "",
  "City": "",
  "State": "",
  "Zip Code": "",
  "Provider": "",
  "Country": "",
  "Whitespace": "",
  "Area": "",
  "Year Built": "",
  "Power": "",
  "Scale": "",
  "Certifications": "",
  "URL": ""
}}
"""

    for attempt in range(retries):
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

            # ✅ Handle empty response by retrying
            if not content or "{" not in content:
                print(f"⚠️ Empty response received (Attempt {attempt + 1}/{retries}). Retrying...")
                sleep(1)
                continue  # Retry the request

            extracted_data = json.loads(content)

            # ✅ Ensure all expected fields exist
            for key in [
                "Name", "Street Address", "City", "State", "Zip Code", "Provider",
                "Country", "Whitespace", "Area", "Year Built", "Power", "Scale",
                "Certifications", "URL"
            ]:
                if key not in extracted_data:
                    extracted_data[key] = ""

            return extracted_data  # ✅ Return successful response

        except Exception as e:
            print(f"❌ API Error (Attempt {attempt + 1}/{retries}): {e}")
            sleep(1)  # Wait before retrying

    print("❌ API failed after retries. Logging for debugging.")
    log_failed_case(facility_data)
    return {}

def log_failed_case(facility_data, output_file=FAILED_CASES_FILE):
    """Logs failed cases for debugging."""
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"failed_input": facility_data}, indent=2) + "\n")

def load_json(filename: str):
    """Loads JSON data from a file."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename: str, data):
    """Saves JSON data to a file."""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def find_missing_entries(output_data):
    """Finds entries with missing Name and Provider fields."""
    return [entry for entry in output_data if not entry["Name"] or not entry["Provider"]]

def reprocess_missing_entries(input_file: str, output_file: str):
    """
    Identifies missing entries and re-extracts data for them.
    Updates the structured output file.
    """
    input_data = load_json(input_file)
    output_data = load_json(output_file)

    missing_entries = find_missing_entries(output_data)

    if not missing_entries:
        print("✅ No missing entries found. All records are complete.")
        return

    print(f"🔄 Reprocessing {len(missing_entries)} missing entries...")

    for entry in missing_entries:
        unique_key = entry["unique_key"]

        if unique_key in input_data:
            facility_data = input_data[unique_key]
            facility_json_str = json.dumps(facility_data, ensure_ascii=False)
            extracted = extract_fields_from_json(facility_json_str)

            # ✅ Skip update if extraction fails
            if not extracted or extracted["Name"] == "" or extracted["Provider"] == "":
                print(f"⚠️ Skipping {unique_key} - API returned no data.")
                continue

            # ✅ Update missing entry in output file
            entry.update(extracted)
            print(f"✅ Reprocessed {unique_key}")

            # ✅ Immediately save progress
            save_json(output_file, output_data)
            sleep(0.5)  # ✅ Delay to prevent API throttling

    print("✅ Reprocessing complete. Updated file saved.")

def main():
    """Main execution function."""
    reprocess_missing_entries(INPUT_FILE, OUTPUT_FILE)

if __name__ == "__main__":
    main()