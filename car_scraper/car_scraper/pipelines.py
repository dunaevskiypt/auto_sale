# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import scrapy
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from car_scraper.models import Car, Location, SaleStatus, Accident, SessionLocal

from itemadapter import ItemAdapter


class CarScraperPipeline:
    def process_item(self, item, spider):
        return item


class SQLAlchemyPipeline:
    def open_spider(self, spider):
        """Создание соединения с базой данных при старте паука"""
        self.db_session = SessionLocal()
        self.buffer = []  # Буфер для объектов Car
        self.batch_size = 100000  # Кол-во объектов для пакетной вставки

    def close_spider(self, spider):
        """Сохраняем оставшиеся объекты и закрываем соединение"""
        try:
            if self.buffer:
                self.db_session.add_all(self.buffer)
                self.db_session.commit()
                spider.logger.info(f"Committed final {len(self.buffer)} cars.")
        except Exception as e:
            self.db_session.rollback()
            spider.logger.error(f"Error during final commit: {e}")
        finally:
            self.db_session.close()

    def process_item(self, item, spider):
        try:
            # Проверяем, если такой объект уже есть в базе
            existing_car = self.db_session.query(
                Car).filter(Car.id == item['id']).first()
            if existing_car:
                spider.logger.info(
                    f"Car with ID {item['id']} already exists. Skipping...")
                return item

            # Создаём объект Car
            car = Car(
                id=item['id'],
                brand=item['brand'],
                model=item['model'],
                year=item['year'],
                generation=item['generation'],
                price=item['price'],
                mileage=item['mileage'],
                fuel_type=item['fuel_type'],
                transmission=item['transmission'],
                engine_capacity=item['engine_capacity'],
                vin_code=item['vin_code'],
                add_date=item['add_date'],
                update_date=item['update_date'],
                top_lifts=item['top_lifts'],
                location=Location(location_name=item['location']),
                sale_status=SaleStatus(status=item['sale_status']),
                accident=Accident(was_in_accident=item['was_in_accident'])
            )

            # Добавляем в буфер
            self.buffer.append(car)

            # Когда набралось batch_size объектов — сохраняем в базу
            if len(self.buffer) >= self.batch_size:
                self.db_session.add_all(self.buffer)
                self.db_session.commit()
                spider.logger.info(
                    f"Committed batch of {self.batch_size} cars.")
                self.buffer.clear()

        except Exception as e:
            self.db_session.rollback()
            spider.logger.error(f"Error saving car {item['id']}: {e}")

        return item
