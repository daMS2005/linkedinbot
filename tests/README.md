# LinkedIn Post Assistant Tests

This directory contains test files for the LinkedIn Post Assistant application. These tests help you verify that the post generation and LinkedIn API integration are working correctly.

## Test Files

- `test_linkedin_post_generator.py`: Tests the basic post generation functionality with various descriptions.
- `test_linkedin_post_formats.py`: Tests the post generation with specific LinkedIn post formats.
- `test_frustration_innovation_post.py`: Tests the generation of a specific "Frustration to Innovation" post format.
- `run_tests.py`: A script to run all the tests.

## How to Run the Tests

You can run the tests in several ways:

### Run All Tests

```bash
python tests/run_tests.py
```

### Run a Specific Test

```bash
python tests/test_linkedin_post_generator.py
python tests/test_linkedin_post_formats.py
python tests/test_frustration_innovation_post.py
```

## Test Data

The test files contain placeholder data that you can modify to test different scenarios:

- `TEST_POST_DESCRIPTIONS`: General post descriptions for testing.
- `TEST_POST_FORMATS`: Specific post formats for testing.
- `FRUSTRATION_INNOVATION_DESCRIPTION`: A detailed description for the "Frustration to Innovation" post format.

## LinkedIn Test Credentials

Before running the LinkedIn posting tests, you need to update the `LINKEDIN_TEST_CREDENTIALS` in `test_linkedin_post_generator.py` with your actual LinkedIn API credentials:

```python
LINKEDIN_TEST_CREDENTIALS = {
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "redirect_uri": "http://localhost:8000/api/auth/callback",
    "user_id": "your_linkedin_user_id"  # Replace with your actual LinkedIn ID
}
```

## Notes

- These tests are designed to help you verify the functionality of the LinkedIn Post Assistant without having to manually test each feature.
- The tests print the generated posts to the console, so you can review them before posting to LinkedIn.
- The LinkedIn posting tests require valid API credentials and will attempt to create actual posts on your LinkedIn account. 