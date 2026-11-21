import requests
import os
import ipaddress
import argparse

AMAZON_URL = "https://ip-ranges.amazonaws.com/ip-ranges.json"
OUTPUT_FOLDER = "target"


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
    print("[+] Expanding CIDR to individual IPs...")

    # Merge overlapping subnets so each IP is only generated once, already sorted
    networks = ipaddress.collapse_addresses(ipaddress.ip_network(cidr) for cidr in prefixes)

    # IPs are generated one by one while writing instead of being stored in memory
    for net in networks:
        for ip in net:  # every address of the subnet, network and broadcast included
            yield str(ip)


def write_list(items, output_file):
    print(f"[+] Writing {output_file}...")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w") as f:
        for line in items:
            f.write(line + "\n")

    print(f"[✓] Done! File generated : {output_file}")


def ask_user_choice():
    print("What do you want to extract?")
    print("[1] All IP addresses (expand CIDRs) NOTE: The generated file is about 1.4 GB")
    print("[2] Keep the original CIDR subnets")
    while True:
        choice = input("> ").strip()
        if choice in ("1", "2"):
            return choice
        print("Please enter 1 or 2.")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert Amazon ip-ranges.json into a raw list. Without argument, asks what to extract."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--expand", action="store_true", help="all IP addresses (same as choice 1)")
    mode.add_argument("--cidr", action="store_true", help="original CIDR subnets (same as choice 2)")
    return parser.parse_args()


def main():
    args = parse_args()
    if args.expand:
        choice = "1"
    elif args.cidr:
        choice = "2"
    else:
        choice = ask_user_choice()

    data = download_amazon_ranges()
    prefixes = extract_prefixes(data)

    if choice == "1":
        result = expand_ips(prefixes)
        output_file = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges_extended.txt")
    else:
        result = sorted(prefixes, key=ipaddress.ip_network)  # numeric order, not text order
        output_file = os.path.join(OUTPUT_FOLDER, "amazon_ip_ranges.txt")

    write_list(result, output_file)


if __name__ == "__main__":
    main()
