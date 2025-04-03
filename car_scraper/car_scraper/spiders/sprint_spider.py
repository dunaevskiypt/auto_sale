import scrapy
import re
import json
from datetime import datetime
from scrapy.exporters import JsonItemExporter


class SprintParser(scrapy.Spider):
    name = "sprint_spider"
    allowed_domains = ["auto.ria.com"]

    def __init__(self):
        self.file = open("sprint_data.json", "wb")
        self.exporter = JsonItemExporter(
            self.file, ensure_ascii=False, indent=4)
        self.exporter.start_exporting()

    def start_requests(self):
        base_url = "https://auto.ria.com/uk/search/?lang_id=4&page={page}&countpage=100&category_id=1&custom=1&abroad=2"
        for page in range(0, 30):
            url = base_url.format(page=page)
            yield scrapy.Request(url, callback=self.parse)

    def parse(self, response):
        for item in response.css("section.ticket-item"):
            data = self.extract_data(item)
            self.exporter.export_item(data)
            yield data

    def extract_data(self, item):
        title = item.css("a.address::attr(title)").get()
        brand, model, year = self.extract_title_info(title)
        generation = self.extract_text(item, "div.generation span::text")
        price = self.extract_price(item)
        mileage = self.extract_mileage(item)
        fuel_type, transmission, engine_capacity = self.extract_characteristics(
            item)
        location = self.extract_location(item)
        state_number = self.extract_text(item, "span.state-num.ua::text")
        vin_code = self.extract_text(item, "span.label-vin span::text")
        add_date, update_date = self.extract_dates(item)
        was_in_accident = self.extract_accident_status(item)
        top_lifts = self.extract_promotion_level(item)
        sale_status, sale_date = self.extract_sale_status(item)

        return {
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
            "add_date": add_date,
            "update_date": update_date,
            "was_in_accident": was_in_accident,
            "top_lifts": top_lifts,
            "sale_status": sale_status,
            "sale_date": sale_date,
        }

    def extract_title_info(self, title):
        if title:
            parts = title.split(" ", 2)
            brand = parts[0]
            model = parts[1] if len(parts) > 1 else None
            year_match = re.search(r'\b\d{4}\b', title)
            year = int(year_match.group()) if year_match else None
            return brand, model, year
        return None, None, None

    def extract_text(self, item, selector):
        text = item.css(selector).get()
        return text.strip() if text else None

    def extract_price(self, item):
        price_text = item.css("span[data-currency='USD']::text").get()
        return int(price_text.strip().replace(" ", "")) if price_text else None

    def extract_mileage(self, item):
        mileage_text = item.css("li.item-char.js-race::text").get()
        mileage_match = re.search(
            r"(\d+)\s*тис\. км", mileage_text) if mileage_text else None
        return int(mileage_match.group(1)) * 1000 if mileage_match else None

    def extract_characteristics(self, item):
        characteristics = item.css(
            "ul.unstyle.characteristic li.item-char::text").getall()
        fuel_type, transmission, engine_capacity = None, None, None
        for char in characteristics:
            char = char.strip()
            fuel_match = re.match(r"([^,]+)", char)
            if fuel_match and fuel_match.group(1).strip() in ["Бензин", "Дизель", "Газ", "Електро"]:
                fuel_type = fuel_match.group(1).strip()
            engine_match = re.search(r"(\d+[.,]?\d*)\s*л\.", char)
            if engine_match:
                engine_capacity = int(
                    float(engine_match.group(1).replace(',', '.')) * 1000)
            transmission_match = re.match(r"(Автомат|Механіка|Варіатор)", char)
            if transmission_match:
                transmission = transmission_match.group(1).strip()
        return fuel_type, transmission, engine_capacity

    def extract_location(self, item):
        location = item.xpath(
            ".//li[contains(@class, 'js-location')]//text()[normalize-space()]").getall()
        return " ".join(location).strip() if location else None

    def extract_dates(self, item):
        add_date = self.extract_text(
            item, "span[data-add-date]::attr(data-add-date)")
        update_date = self.extract_text(
            item, "span[data-update-date]::attr(data-update-date)")
        return (datetime.strptime(add_date, "%Y-%m-%d %H:%M:%S") if add_date else None,
                datetime.strptime(update_date, "%Y-%m-%d %H:%M:%S") if update_date else None)

    def extract_accident_status(self, item):
        accident = self.extract_text(item, "span.state._red::text")
        return "Був в ДТП" in accident if accident else False

    def extract_promotion_level(self, item):
        promotion = self.extract_text(
            item, "a.item.small-promote-level::attr(title)")
        return int(promotion) if promotion and promotion.isdigit() else 0

    def extract_sale_status(self, item):
        sold_date = self.extract_text(
            item, "span[data-sold-date]::attr(data-sold-date)")
        return ("sold", datetime.strptime(sold_date, "%Y-%m-%d %H:%M:%S")) if sold_date else ("on_sale", None)

    def close(self, reason):
        self.exporter.finish_exporting()
        self.file.close()
