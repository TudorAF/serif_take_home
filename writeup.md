### Approach Considered

Two approaches were considered for this problem. The first was to us the index file to grab a list of unique EINs and then call the API used in the "search EIN" box on anthem website. the API call would look something like:

    curl -XGET -H "Content-type: application/json" 'https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/{specific_EIN}.json

this returns a list of files the seems to follow the following naming conventions state_planType_planName.json.gz. We can thin parse this filtering for "state" = "NY" and "plantype" = 'ppo'.

Pros:

- more exhaustive search
- can be used to match EIN to files
- naming convention seems very strictly followed
  Cons:

- lots and lots of API calls. ~ 142K unique EINs
  - very long running. ~142K EINs Anthem is responding with an API request anywhere from .5-1 second. gives us around 42 minutes for the API calls alone.
- significantly more complex code
  - concurrency for API calls
  - risk of API throttling us due to excessive calls

The second approach is to filter all the `in-network` files directly. This is done by looking for each reporting structure and filtering the `in_network` array. Each of these objects have a description, which Anthem follows a very similar approach for description. Upon inspection for a few different objects there is a "New York - PPO" pattern. Thus we can iterate and parse the description adding the url location to a list.

Pros:

- much simpler code to maintain as we have no API calls to manage
- lower over head for running the code

Cons:

- we might miss some file that don't have 'new york'. For example Empire is a plan in New York that is will not have a "new york" in the description.
- end to end process ~ 15 minutes (not including initial file download)

### Implementation

After playing around with the API call to Anthem's website and generating a list of Unique IDs I decided a first iteration filtering `in-network` directly on the downloaded json. As a POC this could prove out the value of getting this data even with some edge cases missed. Once value is proved exploring a much more complex parsing EIN -> API calls could be made.

With the assumption that the zip file is present in the directory. A `IndexParser` class was implemented to unzip the file into a json file. To stream and parse a large format a library was chosen for efficiency and easy of use. The `ijson` library was used to iterate through nested arrays and objects to retrieved all the in-network objects. Finally implemented logic to test for a state and plan type. Outputting the list to a list to a file.

### Running Locally

1. download the zipped file you want to parse
2. ensure `ijson` and `request` are installed in your python environment

you can then either
Edit the index_parser.py file to add the file path on line 76 and run the file directly from your console with `python index_parser.py`

or open a python console import the index_parser class with the following code snippet:

    ip = IndexParser("FILE_PATH_HERE")
    ip.unzip() # unzips to current directory

    # returns all urls in the in-network objects
    url = ip.get_network_files(state_name='new york', plan_type='ppo')

    # write to a file if you want
    with open("new_york_ppo.txt", "w") as f:
        for item in url:
            f.write(str(item) + "\n")

# Notes

I implemented the threaded API calls as well. It seamed as though I would get throttled after a few thousand request. To fix this we could to a cool down feature but but this lengthen run greatly. Also some API calls where failing with valid TIN results.

I left the code to do some API calls in for the sake of the exercise. Some optimizations to be made to not parse the unique ein upon initializations.
