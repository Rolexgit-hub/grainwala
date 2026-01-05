import json

# JSON parsing for product rows
def process_rows(rows):
    products = []
    for row in rows:
        product = list(row)
        if len(product) > 8:
            weights_json = product[8] if product[8] else '[]'
            try:
                product[8] = json.loads(weights_json)
            except json.JSONDecodeError:
                product[8] = []
        else:
            product.append([])
        products.append(product)
    return products

# Name initials
def get_initials(name):
    parts = name.split()
    return "".join([p[0].upper() for p in parts if p])
