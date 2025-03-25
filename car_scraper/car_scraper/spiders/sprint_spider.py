import scrapy
import re


class SprintParser(scrapy.Spider):
    name = "sprint_spider"
    allowed_domains = ["auto.ria.com"]
    start_urls = [
        "https://auto.ria.com/uk/legkovie/?page=1"
    ]

    def parse(self, response):
        # Parse only brand, model, year, generation, price, mileage, location, fuel type, transmission, engine capacity, state number, VIN
        for item in response.css("section.ticket-item"):
            # Extract title attribute to get brand, model, and year
            title = item.css("a.address::attr(title)").get()
            if title:
                title_parts = title.split(" ", 2)
                brand = title_parts[0]
                model = title_parts[1] if len(title_parts) > 1 else None

                # Extract year (4 digits)
                year_match = re.search(r'\b\d{4}\b', title)
                year = year_match.group() if year_match else None
            else:
                brand, model, year = None, None, None

            # Extract generation from the "generation" class span
            generation = item.css("div.generation span::text").get()
            if generation:
                generation = generation.strip().replace("покоління", "generation")
            else:
                generation = None

            # Extract price and remove spaces and currency
            price_text = item.css("span[data-currency='USD']::text").get()
            if price_text:
                price = int(price_text.strip().replace(" ", ""))
            else:
                price = None

            # Extract mileage and convert to number (e.g., "267 тис. км" to 267000)
            mileage_text = item.css("li.item-char.js-race::text").get()
            if mileage_text:
                mileage_match = re.search(r"(\d+)\s*тис\. км", mileage_text)
                if mileage_match:
                    mileage = int(mileage_match.group(1)) * 1000
                else:
                    mileage = None
            else:
                mileage = None

            # Extract characteristics (fuel type, transmission, engine capacity)
            characteristics = item.css(
                "ul.unstyle.characteristic li.item-char::text").getall()
            fuel_type = None
            transmission = None
            engine_capacity = None

            for char in characteristics:
                char = char.strip()

                # Extract fuel type (everything before the comma or without a comma)
                fuel_match = re.match(r"([^,]+)", char)
                if fuel_match:
                    potential_fuel = fuel_match.group(1).strip()

                    # Check if it's a known fuel type
                    known_fuel_types = [
                        "Бензин", "Дизель", "Газ", "Газ пропан-бутан", "Газ метан", "Електро",
                        "Гібрид (HEV)", "Гібрид (PHEV)", "Гібрид (MHEV)"
                    ]
                    if potential_fuel in known_fuel_types or "/" in potential_fuel:
                        fuel_type = potential_fuel

                # Extract engine capacity (like "2 л." or "4.66 л.")
                engine_capacity_match = re.search(r"(\d+[.,]?\d*)\s*л\.", char)
                if engine_capacity_match:
                    engine_capacity = float(
                        engine_capacity_match.group(1).replace(',', '.')) * 1000
                    engine_capacity = int(engine_capacity)

                # Extract transmission (e.g., "Автомат", "Варіатор", "Механіка")
                transmission_match = re.match(
                    r"(Автомат|Варіатор|Механіка|Робот)", char)
                if transmission_match:
                    transmission = transmission_match.group(1).strip()

            # Extract location more reliably
            location = item.xpath(
                ".//li[contains(@class, 'item-char view-location js-location')]//text()[normalize-space()]"
            ).getall()
            if location:
                location = " ".join(location).strip()
                location = re.sub(r"\s*\(.*?\)\s*|\)$", "", location)
            else:
                location = None

            # Extract state number (remove spaces)
            state_number = item.css(
                "div.base_information span.state-num::text").get()
            if state_number:
                state_number = state_number.strip().replace(" ", "")
            else:
                state_number = None

            # Extract VIN code
            vin_code = item.css(
                "div.base_information span.label-vin span::text").get()
            if vin_code:
                vin_code = vin_code.strip()
            else:
                vin_code = None

            # Prepare and yield the data
            data = {
                "id": item.attrib.get("data-advertisement-id"),
                "brand": brand,
                "model": model,
                "year": year,
                "generation": generation,
                "price": price,
                "mileage": mileage,
                "fuel_type": fuel_type,
                "transmission": transmission,
                "engine_capacity": engine_capacity,
                "location": location,
                "state_number": state_number,
                "vin_code": vin_code
            }
            yield data
