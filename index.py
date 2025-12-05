import requests
import os

AMAZON_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
OUTPUT_FOLDER = "target"
OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges.txt")


def download_amazon_ranges():
    print("[+] Downloading...")
    r = requests.get(AMAZON_URL, timeout=10)
    r.raise_for_status()
    return r.json()


def extract_prefixes(data):
    prefixes = set()
    print("[+] Extracting IPv4 prefixes (ip_prefix)...")
    for entry in data.get("prefixes", []):  # IPv4 section
        if "ip_prefix" in entry:
            prefixes.add(entry["ip_prefix"])
    return prefixes


def write_prefixes(prefixes, output_file):
    print(f"[+] Writing {output_file}...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        for cidr in sorted(prefixes):
            f.write(cidr + "\n")

    print(f"[✓] Done! File generated : {output_file}")


def main():
    data = download_amazon_ranges()
    prefixes = extract_prefixes(data)
    write_prefixes(prefixes, OUTPUT_FILE)


if __name__ == "__main__":
    main()
