# type: ignore
import configparser
import logging
import random
import time

import allure
import pytest
import requests

logger = logging.getLogger(__name__)

config = configparser.ConfigParser()
config.read("qa-pytest-examples/resources/terminalx-default-config.ini")
API_URL = config.get("api", "url", fallback="https://petstore.swagger.io/v2")


def random_pet():
    return {
        "id": random.randint(10000, 99999),
        "name": f"pet{random.randint(1, 1000)}",
        "status": "available"
    }


def add_pet(session, pet, retries=3, delay=1.0):
    url = f"{API_URL}/pet"
    logger.info("POST %s %s", url, pet)
    last_exc = None
    with allure.step(f"Add pet {pet['id']} via API"):
        for attempt in range(retries):
            try:
                response = session.post(url, json=pet, timeout=10)
                response.raise_for_status()
                return
            except Exception as exc:
                logger.warning("add_pet failed (attempt %d/%d): %s",
                               attempt+1, retries, exc)
                last_exc = exc
                time.sleep(delay)
        logger.error("add_pet failed after %d attempts", retries)
        raise last_exc


def get_available_pets(session):
    url = f"{API_URL}/pet/findByStatus"
    logger.info("GET %s", url)
    with allure.step("Get available pets via API"):
        response = session.get(url, params={"status": "available"}, timeout=10)
        response.raise_for_status()
        return response.json()


def wait_for_pet(session, pet_id, timeout=10.0, interval=0.5):
    logger.info("Waiting for pet with id %s", pet_id)
    with allure.step(f"Wait for pet with id {pet_id} to appear"):
        end_time = time.monotonic() + timeout
        while time.monotonic() < end_time:
            pets = get_available_pets(session)
            if any(p["id"] == pet_id for p in pets):
                logger.info("Pet with id %s found", pet_id)
                return
            logger.debug("Pet with id %s not found yet, retrying...", pet_id)
            time.sleep(interval)
        logger.error("Pet with id %s not found after %s seconds",
                     pet_id, timeout)
        raise AssertionError(
            f"Pet with id {pet_id} not found after {timeout} seconds")


@pytest.mark.external
@allure.title("Imperative: Add and verify pet in Swagger Petstore API")
def should_add_and_verify_pet():
    session = requests.Session()
    pet = random_pet()
    with allure.step("Add pet via API"):
        add_pet(session, pet)
    wait_for_pet(session, pet["id"])
    logger.info("Test completed for pet: %s", pet)
