import scrapy
import re
from datetime import datetime


class SprintParser(scrapy.Spider):
    name = "sprint_spider"
    allowed_domains = ["auto.ria.com"]

    def start_requests(self):
        base_url = "https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
        for page in range(0, 30):
            url = base_url.format(page=page)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        # Parse each listing
        for item in response.css("section.ticket-item"):
            # Extract title for brand, model, and year
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

            # Extract generation
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

            # Extract mileage and convert to a number (e.g., "267 тис. км" -> 267000)
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

                # Extract fuel type
                fuel_match = re.match(r"([^,]+)", char)
                if fuel_match:
                    potential_fuel = fuel_match.group(1).strip()

                    # Check if it matches a known fuel type
                    known_fuel_types = [
                        "Бензин", "Дизель", "Газ", "Газ пропан-бутан", "Газ метан", "Електро",
                        "Гібрид (HEV)", "Гібрид (PHEV)", "Гібрид (MHEV)"
                    ]
                    if potential_fuel in known_fuel_types or "/" in potential_fuel:
                        fuel_type = potential_fuel

                # Extract engine capacity (e.g., "2 л." or "4.66 л.")
                engine_capacity_match = re.search(r"(\d+[.,]?\d*)\s*л\.", char)
                if engine_capacity_match:
                    engine_capacity = float(
                        engine_capacity_match.group(1).replace(',', '.')) * 1000
                    engine_capacity = int(engine_capacity)

                # Extract transmission type (e.g., "Автомат", "Варіатор", "Механіка")
                transmission_match = re.match(
                    r"(Автомат|Варіатор|Механіка|Робот|Типтронік)", char)
                if transmission_match:
                    transmission = transmission_match.group(1).strip()

            # Extract location
            location = item.xpath(
                ".//li[contains(@class, 'item-char view-location js-location')]//text()[normalize-space()]"
            ).getall()
            if location:
                location = " ".join(location).strip()
                location = re.sub(r"\s*\(.*?\)\s*|\)$", "",
                                  location)  # Clean location
            else:
                location = None

            # Extract state number (license plate)
            state_number = item.css("span.state-num.ua::text").get()
            if state_number:
                state_number = state_number.strip().replace(
                    " ", "")  # Remove spaces in the state number

            # Extract VIN code
            vin_code = item.css("span.label-vin span::text").get()
            if vin_code:
                vin_code = vin_code.strip()

            # Extract the date of publication and the date of last update
            add_date = item.css(
                "span[data-add-date]::attr(data-add-date)").get()
            update_date = item.css(
                "span[data-update-date]::attr(data-update-date)").get()

            # Convert the date format
            if add_date:
                add_date = add_date.strip()
                add_date_obj = datetime.strptime(add_date, "%Y-%m-%d %H:%M:%S")
            if update_date:
                update_date = update_date.strip()
                update_date_obj = datetime.strptime(
                    update_date, "%Y-%m-%d %H:%M:%S")

            # Check if the car was in an accident
            accident = item.css("span.state._red::text").get()
            if accident and "Був в ДТП" in accident:
                was_in_accident = True
            else:
                was_in_accident = False

            # Extract promotion level (top lifts) from the <a class="item small-promote-level"> element
            promotion = item.css(
                "a.item.small-promote-level::attr(title)").get()
            # Use the promotion level directly if available
            top_lifts = promotion if promotion else 0
            if top_lifts:
                # Convert to integer if it's a valid number
                top_lifts = int(top_lifts)
            else:
                top_lifts = 0  # If no promotion level found, assume 0 lifts

            # Extract sale status and sale date
            sale_status = "on_sale"
            sale_date = None

            # Check if the car is sold
            sold_date = item.css(
                "span[data-sold-date]::attr(data-sold-date)").get()
            if sold_date:
                sale_status = "sold"
                sale_date = datetime.strptime(
                    sold_date.strip(), "%Y-%m-%d %H:%M:%S")
                add_date_obj = None
                update_date_obj = None  # Remove add and update dates if the car is sold

            # Prepare and yield the extracted data
            yield {
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
                "vin_code": vin_code,
                "add_date": add_date_obj if add_date else None,
                "update_date": update_date_obj if update_date else None,
                "was_in_accident": was_in_accident,
                "top_lifts": top_lifts,
                # Include the sale status (on_sale or sold)
                "sale_status": sale_status,
                # Include sale date only if sold
                "sale_date": sale_date if sale_status == "sold" else None
            }
