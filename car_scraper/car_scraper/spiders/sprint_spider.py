import scrapy
import re


class SprintParser(scrapy.Spider):
    name = "sprint_spider"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/legkovie/?page=140"
    ]

    def parse(self, response):
        # Parse only brand, model, year, generation, price, mileage
        for item in response.css("section.ticket-item"):
            # Extract title attribute to get brand, model, and year
            title = item.css("a.address::attr(title)").get()
            if title:
                # Title format is like "Toyota Venza 2013 in Kyiv"
                # Split by spaces to separate brand and model
                title_parts = title.split(" ", 2)
                brand = title_parts[0]
                model = title_parts[1] if len(title_parts) > 1 else None

                # Use regular expression to extract the year (4 digits)
                # Find 4-digit number
                year_match = re.search(r'\b\d{4}\b', title)
                year = year_match.group() if year_match else None
            else:
                brand, model, year = None, None, None

            # Extract generation from the "generation" class span
            generation = item.css("div.generation span::text").get()
            if generation:
                # Replace 'покоління' with 'generation'
                generation = generation.strip().replace("покоління", "generation")
            else:
                generation = None

            # Extract price and remove spaces and currency
            price_text = item.css("span[data-currency='USD']::text").get()
            if price_text:
                # Remove spaces and convert to int
                price = int(price_text.strip().replace(" ", ""))
            else:
                price = None

            # Extract mileage and convert to number (e.g., "6 тис. км" to 6000)
            mileage_text = item.css("li.item-char.js-race::text").get()
            if mileage_text:
                mileage_match = re.search(r"(\d+)\s*тис\. км", mileage_text)
                if mileage_match:
                    mileage = int(mileage_match.group(1)) * \
                        1000  # Convert to actual mileage
                else:
                    mileage = None
            else:
                mileage = None

            data = {
                "id": item.attrib.get("data-advertisement-id"),
                "brand": brand,
                "model": model,
                "year": year,
                "generation": generation,  # Add generation to the extracted data
                "price": price,  # Add price as an integer
                "mileage": mileage  # Add mileage as an integer
            }
            yield data
