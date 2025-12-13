import requests
import os
import ipaddress

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


def expand_ips(prefixes):
    all_ips = set()
    print("[+] Expanding CIDR to individual IPs...")

    for cidr in prefixes:
        net = ipaddress.ip_network(cidr)
        for ip in net.hosts():
            all_ips.add(str(ip))

    return all_ips


def write_list(items, output_file):
    print(f"[+] Writing {output_file}...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        for line in sorted(items):
            f.write(line + "\n")

    print(f"[✓] Done! File generated : {output_file}")


def ask_user_choice():
    print("What do you want to extract?")
    print("[1] All IP addresses (expand CIDRs) NOTE: This option currently uses up to 11 GB of RAM to run")
    print("[2] Keep the original CIDR subnets")
    while True:
        choice = input("> ").strip()
        if choice in ("1", "2"):
            return choice
        print("Please enter 1 or 2.")


def main():
    choice = ask_user_choice()
    data = download_amazon_ranges()
    prefixes = extract_prefixes(data)

    if choice == "1":
        result = expand_ips(prefixes)
        OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges_extended.txt")
    else:
        result = prefixes
        OUTPUT_FILE = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges.txt")

    write_list(result, OUTPUT_FILE)


if __name__ == "__main__":
    main()
