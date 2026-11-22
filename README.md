# Amazon IP Ranges

Amazon provides a list of the IP addresses they use in a public file called ip-ranges.json, which is available directly on their website https://ip-ranges.amazonaws.com/ip-ranges.json.

I needed to convert this file into a RAW file for a specific use, which is why I created this Python program that takes this file and converts it to give me what I want.

These files are updated automatically every day (around 6:00, Paris time) by a GitHub Actions workflow, only when Amazon changes its ranges. If you want to generate them yourself, feel free to clone this project.

- Original CIDR subnets:
  > https://raw.githubusercontent.com/Baba0bab/Amazon-IP-Ranges/refs/heads/main/target/amazon_ip_ranges.txt
- Without nested subnets:
  > https://raw.githubusercontent.com/Baba0bab/Amazon-IP-Ranges/refs/heads/main/target/amazon_ip_ranges_dedupe.txt
- Compact (merged subnets, shortest list):
  > https://raw.githubusercontent.com/Baba0bab/Amazon-IP-Ranges/refs/heads/main/target/amazon_ip_ranges_compact.txt

The list of every single IP address (`--expand`) is too big for GitHub (about 1.5 GB), you have to generate it yourself.

## Usage

Requires Python 3.

```
pip install -r requirements.txt
python index.py
```

Without argument, the program asks what you want to extract. You can also choose directly with an argument:

| Argument | Choice | Output file (in `target/`) | Content |
|---|---|---|---|
| `--expand` | 1 | `amazon_ip_ranges_extended.txt` | Every single IP address (about 1.5 GB) |
| `--cidr` | 2 | `amazon_ip_ranges.txt` | Original CIDR subnets published by Amazon |
| `--dedupe` | 3 | `amazon_ip_ranges_dedupe.txt` | Original subnets, without the ones already included in a bigger one |
| `--compact` | 4 | `amazon_ip_ranges_compact.txt` | Overlapping and adjacent subnets merged, shortest list |

All files cover exactly the same IP addresses (IPv4 only), sorted in numeric order.

Example: `python index.py --compact`
