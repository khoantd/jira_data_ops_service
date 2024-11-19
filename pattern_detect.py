"""
Pattern Detection Module for JIRA Ticket Analysis
This module handles pattern detection and categorization of text content from JIRA tickets.
"""

import re
import json
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from datetime import datetime


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class Pattern:
    """Data class for pattern definition with type hints"""
    pattern_type: str
    regex: str
    confidence: float
    description: str = ""
    priority: int = 0


class PatternMatcherConfig:
    """
    Configuration management for pattern matching.
    Handles loading and validation of pattern configurations from files or defaults.
    """

    DEFAULT_CATEGORY_REQUIREMENTS = {
        "Loan Application Error": {
            "required_patterns": ["crm_number", "phone_number", "personal_id"],
            "priority": 100,
            "description": "Issues related to loan application processing"
        },
        "Cannot do Loan Onboarding": {
            "required_patterns": ["phone_number", "personal_id", "customer_name"],
            "priority": 90,
            "description": "Problems with loan onboarding process"
        },
        "Application Issue": {
            "required_patterns": ["application_id", "customer_name"],
            "priority": 80,
            "description": "General application-related issues"
        },
        "General Support Request": {
            "required_patterns": ["formal_request"],
            "priority": 70,
            "description": "General IT support requests"
        }
    }

    @classmethod
    def load_patterns(cls, config_path: str = 'config/input_patterns.json') -> List[Pattern]:
        """
        Load and validate patterns from configuration file or use defaults.

        Args:
            config_path: Path to the pattern configuration file

        Returns:
            List[Pattern]: List of validated Pattern objects

        Raises:
            ValueError: If pattern data is invalid
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(
                    f"Config file not found at {config_path}. Using defaults.")
                return cls._get_default_patterns()

            with config_file.open('r', encoding='utf-8') as file:
                patterns_data = json.load(file)

                # Validate patterns data structure
                if isinstance(patterns_data, dict) and 'patterns' in patterns_data:
                    patterns_list = patterns_data['patterns']
                elif isinstance(patterns_data, list):
                    patterns_list = patterns_data
                else:
                    logger.warning(
                        "Invalid patterns data format. Using defaults.")
                    return cls._get_default_patterns()

                # Validate and create Pattern objects
                validated_patterns = []
                for pattern_dict in patterns_list:
                    try:
                        # Validate required fields
                        required_fields = {
                            'pattern_type', 'regex', 'confidence'}
                        if not all(field in pattern_dict for field in required_fields):
                            raise ValueError(
                                f"Missing required fields in pattern: {pattern_dict}")

                        # Validate regex pattern
                        try:
                            re.compile(pattern_dict['regex'])
                        except re.error as e:
                            raise ValueError(f"Invalid regex pattern: {e}")

                        # Validate confidence value
                        if not 0 <= pattern_dict['confidence'] <= 1:
                            raise ValueError(
                                "Confidence must be between 0 and 1")

                        pattern = Pattern(**pattern_dict)
                        validated_patterns.append(pattern)
                    except Exception as e:
                        logger.error(
                            f"Error validating pattern {pattern_dict}: {str(e)}")
                        continue

                if not validated_patterns:
                    logger.warning("No valid patterns found. Using defaults.")
                    return cls._get_default_patterns()

                return validated_patterns

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {config_path}: {str(e)}")
            return cls._get_default_patterns()
        except Exception as e:
            logger.error(f"Unexpected error loading patterns: {str(e)}")
            return cls._get_default_patterns()

    @staticmethod
    def _get_default_patterns() -> List[Pattern]:
        """Get default pattern configurations"""
        return [
            Pattern(
                pattern_type="formal_request",
                regex=r"(?i)\b(dear IT|Nhờ IT hỗ trợ|nhờ IT|nhờ anh IT)\b",
                confidence=0.9,
                description="Formal IT support request identifier",
                priority=100
            ),
            Pattern(
                pattern_type="crm_number",
                regex=r"\b(CRM:|Crm ID:|CRM ID:|Crm:)\s*(\d+)\b",
                confidence=0.85,
                description="Customer CRM number",
                priority=90
            ),
            Pattern(
                pattern_type="phone_number",
                regex=r"\b(Sđt:|SDT)\s*(\d{9,15})\b",
                confidence=0.8,
                description="Customer phone number",
                priority=80
            ),
            Pattern(
                pattern_type="personal_id",
                regex=r"\b(CCCD:|CCCD)\s*(\d+)\b",
                confidence=0.8,
                description="Personal identification number",
                priority=70
            ),
            Pattern(
                pattern_type="customer_name",
                regex=r"(?i)(?:KH:|KH)\s+([A-ZĐÀÁẢÃẠÈÉẺẼẸÌÍỈĨỊÒÓỎÕỌÙÚỦŨỤỲÝỶỸỴ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+(?:\s+[A-ZĐÀÁẢÃẠÈÉẺẼẸÌÍỈĨỊÒÓỎÕỌÙÚỦŨỤỲÝỶỸỴ][a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]+){1,6})(?=\s*[-\s]|$)",
                confidence=0.8,
                description="Customer name",
                priority=60
            ),
            Pattern(
                pattern_type="application_id",
                regex=r"\b(APP ID:|APP)\s*(\d+)\b",
                confidence=0.8,
                description="Application ID",
                priority=50
            )
        ]

    @classmethod
    def load_category_requirements(cls, config_path: str = 'config/category_requirements.json') -> Dict:
        """
        Load category requirements from configuration file or use defaults.

        Args:
            config_path: Path to the category requirements configuration file

        Returns:
            Dict: Category requirements configuration
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(
                    f"Category requirements file not found at {config_path}. Using defaults.")
                return cls.DEFAULT_CATEGORY_REQUIREMENTS

            with config_file.open('r', encoding='utf-8') as file:
                category_data = json.load(file)

                # Validate category data
                if not isinstance(category_data, dict):
                    raise ValueError(
                        "Category requirements must be a dictionary")

                for category, requirements in category_data.items():
                    if not isinstance(requirements, dict):
                        raise ValueError(
                            f"Invalid requirements format for category: {category}")
                    if "required_patterns" not in requirements:
                        raise ValueError(
                            f"Missing required_patterns for category: {category}")
                    if not isinstance(requirements["required_patterns"], list):
                        raise ValueError(
                            f"required_patterns must be a list for category: {category}")

                return category_data

        except Exception as e:
            logger.error(f"Error loading category requirements: {str(e)}")
            return cls.DEFAULT_CATEGORY_REQUIREMENTS


class PatternMatcher:
    """Pattern matching and categorization handler"""

    def __init__(self):
        """Initialize pattern matcher with configurations"""
        self.patterns = PatternMatcherConfig.load_patterns()
        self.category_requirements = PatternMatcherConfig.load_category_requirements()

    def determine_category(self, extracted_values: Dict[str, str]) -> str:
        """
        Determine the category based on extracted patterns

        Args:
            extracted_values: Dictionary of pattern types and their extracted values

        Returns:
            str: Determined category or "Uncategorized"
        """
        detected_patterns = set(extracted_values.keys())

        # Sort categories by priority
        sorted_categories = sorted(
            self.category_requirements.items(),
            key=lambda x: x[1].get('priority', 0),
            reverse=True
        )

        # Check each category's requirements
        for category, requirements in sorted_categories:
            required_patterns = set(requirements.get('required_patterns', []))
            if required_patterns.issubset(detected_patterns):
                return category

        return "Uncategorized"

    def detect_patterns(self, text: str) -> Dict[str, Any]:
        """
        Detect patterns in text and extract values

        Args:
            text: Input text to analyze

        Returns:
            Dict containing matches, extracted values, and category
        """
        if not isinstance(text, str) or not text.strip():
            return {
                "matches": [],
                "extracted_values": {},
                "category": "Uncategorized"
            }

        matches = []
        extracted_values = {}

        try:
            # Process patterns
            for pattern in sorted(self.patterns, key=lambda x: x.priority, reverse=True):
                for match in re.finditer(pattern.regex, text, re.IGNORECASE):
                    match_data = self._process_match(match, pattern)
                    if match_data and isinstance(match_data, dict):
                        matches.append(match_data)
                        extracted_value = match_data.get("extracted_value")
                        if extracted_value is not None:
                            extracted_values[pattern.pattern_type] = extracted_value

            # Determine category
            category = self.determine_category(extracted_values)

            return {
                "matches": matches,
                "extracted_values": extracted_values,
                "category": category,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logger.error(f"Error in pattern detection: {str(e)}")
            return {
                "matches": [],
                "extracted_values": {},
                "category": "Uncategorized"
            }

    def _process_match(self, match: re.Match, pattern: Pattern) -> Optional[Dict[str, Any]]:
        """Process a regex match and extract relevant data"""
        try:
            if pattern.pattern_type == "customer_name":
                name_match = match.group(1)
                if name_match:
                    return {
                        "pattern_type": pattern.pattern_type,
                        "token": name_match.strip(),
                        "extracted_value": name_match.strip(),
                        "confidence": pattern.confidence,
                        "priority": pattern.priority
                    }
            elif pattern.pattern_type == "application_id":
                app_id = match.group(
                    2) if match.lastindex and match.lastindex >= 2 else None
                if app_id:
                    return {
                        "pattern_type": pattern.pattern_type,
                        "token": match.group(),
                        "extracted_value": app_id.strip(),
                        "confidence": pattern.confidence,
                        "priority": pattern.priority
                    }
            else:
                value = match.group(
                    2) if match.lastindex and match.lastindex >= 2 else match.group(1)
                if value:
                    return {
                        "pattern_type": pattern.pattern_type,
                        "token": match.group(),
                        "extracted_value": value.strip(),
                        "confidence": pattern.confidence,
                        "priority": pattern.priority
                    }
            return None
        except Exception as e:
            logger.error(f"Error processing match: {str(e)}")
            return None


def process_csv_file(input_file: str, output_file: str) -> None:
    """Process CSV file and extract patterns"""
    try:
        df = pd.read_csv(input_file)
        pattern_matcher = PatternMatcher()

        # Initialize empty lists for results
        extracted_values_list = []
        categories_list = []

        for _, row in df.iterrows():
            text = str(row.get('Description', ''))
            if pd.isna(text) or not text.strip():
                # Handle empty/NaN descriptions
                extracted_values_list.append({})
                categories_list.append("Uncategorized")
                continue

            try:
                detection_result = pattern_matcher.detect_patterns(text)

                # Extract values and category from detection result
                extracted_values = detection_result.get(
                    "extracted_values", {}) if isinstance(detection_result, dict) else {}
                category = detection_result.get("category", "Uncategorized") if isinstance(
                    detection_result, dict) else "Uncategorized"

                extracted_values_list.append(extracted_values)
                categories_list.append(category)

            except Exception as e:
                logger.error(f"Error processing text: {str(e)}")
                extracted_values_list.append({})
                categories_list.append("Uncategorized")

        # Create DataFrame from results
        results_df = pd.DataFrame(extracted_values_list)

        # Add category column
        results_df['Category'] = categories_list

        # Merge with original DataFrame
        output_df = pd.concat([df, results_df], axis=1)

        # Reorder columns to put Category near the beginning
        cols = output_df.columns.tolist()
        if 'Category' in cols:
            cols.remove('Category')
            cols.insert(2, 'Category')  # Insert after Description
            output_df = output_df[cols]

        # Save to CSV
        output_df.to_csv(output_file, index=False)
        logger.info(
            f"Successfully processed {len(df)} rows and saved to {output_file}")

    except Exception as e:
        logger.error(f"Error processing CSV file: {str(e)}")


if __name__ == "__main__":
    process_csv_file(
        'data/ml_data/jira_closed_tickets_batch_1.csv',
        'data/ml_data/output/output_jira_closed_tickets_batch_1.csv'
    )
