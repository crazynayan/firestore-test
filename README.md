# Tests for Firestore ORM

The test cases for the [Firestore ORM (firestore-ci)](https://github.com/crazynayan/firestore)
The test cases are in the test folder. They are self explanatory. 
Review them to understand firestore-ci better.

## How to use?
1. Install firestore-ci `pip install firestore-ci`
2. Save the GCP service-account json key in your project folder & give it the name `google-cloud.json`
3. Run the test case `python -m unittest discover -s test -v -f`