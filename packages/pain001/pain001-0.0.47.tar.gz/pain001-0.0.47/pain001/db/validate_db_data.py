# Copyright (C) 2023-2026 Sebastien Rousseau.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Any

# Configure the logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.ERROR)


def validate_db_data(data: list[dict[str, Any]]) -> bool:
    """
    Validate the data from a database.

    Args:
        data (list of dict): The data to validate.

    Returns:
        bool: True if the data is valid, False otherwise.
    """
    # Core required fields that must be present and non-null
    required_columns = [
        "id",
        "date",
        "nb_of_txs",
        "initiator_name",
        "payment_information_id",
        "payment_method",
        "debtor_name",
        "debtor_account_IBAN",
        "payment_amount",
        "currency",
        "creditor_name",
        "creditor_account_IBAN",
    ]

    for row in data:
        # Check only required columns
        for column in required_columns:
            if column not in row or row[column] is None or row[column] == "":
                logger.error(
                    "Error: Missing value for required column '%s' in row: %s",
                    column,
                    row,
                )
                return False
    return True
