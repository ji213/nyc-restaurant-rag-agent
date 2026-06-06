import os
import json
import ast

def clean_yelp_value(val_str):
    """Strips Yelp's legacy unicode 'u' prefixes and outer quotes."""
    s = val_str.strip()
    if (s.startswith("u'") and s.endswith("'")) or (s.startswith('u"') and s.endswith('"')):
        s = s[2:-1]
    if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
        s = s[1:-1]
    return s.strip()

def process_and_normalize_sample():
    print("=" * 70)
    print("Dynamic Attribute Discovery & Flattening Engine (Hardened Checkpoint 1)")
    print("=" * 70)

    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    biz_path = os.path.join(base_dir, 'Data', 'yelp_academic_dataset_business.json')
    review_path = os.path.join(base_dir, 'Data', 'yelp_academic_dataset_review.json')

    if not os.path.exists(biz_path) or not os.path.exists(review_path):
        print("❌ ERROR: Source files missing.")
        return

    philly_biz = {}
    restaurant_keywords = {"Restaurants", "Food", "Bars", "Eateries", "Cafes", "Bakeries"}

    with open(biz_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            biz = json.loads(line)
            
            # only process json lines for philly
            if biz.get("city", "").strip().lower() != "philadelphia":
                continue
                
            cats_raw = biz.get("categories") or ""
            cats_list = [c.strip() for c in cats_raw.split(",")] if cats_raw else []
            
            ## check to see if ant categories match the restaurant categories list
            if not any(kw in cats_list for kw in restaurant_keywords):
                continue

            # ─── HARDENED DYNAMIC ATTRIBUTE INSPECTION ENGINE ───
            feature_flags = []
            raw_attrs = biz.get("attributes") or {}
            
            if raw_attrs and isinstance(raw_attrs, dict):
                for key, val in raw_attrs.items():
                    # Ex: "BusinessParking": "{'garage': False, 'street': False, 'validated': False, 'lot': True, 'valet': False}"

                    # Clean key, remove redundant words like Restaurants and Businesss from key
                    # Ex: "BusinessParking" -> "Parking"
                    clean_key = key.replace("Restaurants", "").replace("Business", "")
                    val_str = str(val).strip()
                    
                    # Case 1: Detect and parse nested stringified dictionaries
                    if val_str.startswith("{") and val_str.endswith("}"):
                        try:
                            # Safely convert raw text '{'romantic': False...}' into a true Python dict
                            # EX: nested_dict = {"garage": False, "street": False, "validated": False, "lot": True, "valet": False}
                            nested_dict = ast.literal_eval(val_str)
                            # for key value pair in nested_dict
                            for sub_key, sub_val in nested_dict.items():
                                sub_val_clean = clean_yelp_value(str(sub_val))
                                if sub_val_clean == "True":
                                    # EX: append Parking_lot
                                    feature_flags.append(f"{clean_key}_{sub_key}")
                                elif sub_val_clean not in ["False", "None", "{}"]:
                                    # For text values that aren't True, False, None, or {}, append the descriptive string
                                    feature_flags.append(f"{clean_key}_{sub_key}_{sub_val_clean}")
                        except Exception:
                            # Fallback if literal_eval fails on malformed lines
                            feature_flags.append(f"{clean_key}_{val_str}")
                    
                    # Case 2: Simple Boolean Flags
                    elif val_str == "True":
                        feature_flags.append(clean_key)
                    
                    # Case 3: Simple Value Pairs (e.g. Alcohol_full_bar)
                    elif val_str not in ["False", "None", "{}"]:
                        clean_v = clean_yelp_value(val_str)
                        if clean_v:
                            feature_flags.append(f"{clean_key}_{clean_v}")

            # grab business id
            bid = biz.get("business_id")

            #instant indexing using bid
            philly_biz[bid] = {
                "name": biz.get("name"),
                "address": biz.get("address"),
                "postalcode": biz.get("postal_code", "").strip(),
                "latitude": float(biz.get("latitude")) if biz.get("latitude") is not None else None,
                "longitude": float(biz.get("longitude")) if biz.get("longitude") is not None else None,
                "stars_business": float(biz.get("stars", 0)),
                "categories": cats_list,
                "features": feature_flags
            }

    # 2. Match Reviews (Keep limit at 3 for local visual auditing)
    normalized_payloads = []
    with open(review_path, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            rev = json.loads(line)
            bid = rev.get("business_id")
            
            # check if the bid in the review lines up with the busiess dict
            if bid in philly_biz:
                meta = philly_biz[bid]

                # Combine address components
                display_address = f"{meta['address']}, Philadelphia, PA {meta['postalcode']}"

                payload = {
                    "id": rev.get("review_id"),
                    "metadata": {
                        "business_id": bid,
                        "restaurant_name": meta["name"],
                        "full_address": display_address,
                        "postal_code": meta["postalcode"],
                        "latitude": meta['latitude'],
                        "longitude": meta['longitude'],
                        "review_stars": float(rev.get("stars", 0)),
                        "stars_business": meta["stars_business"],
                        "categories": meta["categories"],
                        "features": meta["features"],
                        "review_text": rev.get("text").replace("\n", " ").strip()
                    }
                }
                normalized_payloads.append(payload)
                if len(normalized_payloads) >= 10:
                    break

    print(json.dumps(normalized_payloads, indent=2))
    print(f"\n✅ Clean blueprint successfully flattened and verified!")

if __name__ == "__main__":
    process_and_normalize_sample()