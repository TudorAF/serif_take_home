import gzip
import shutil
import requests
import multiprocessing.pool
# stream parsing json
import ijson


class IndexParser:
    ''' Takes a zipped file unzips to a new file and then can parse for urls given a state and plan type '''

    def __init__(self, index_path):
        self.index_path = index_path
        self.json_file_name = index_path.split('.')[0] + '.json'
        self.unique_ein = self._unique_ein()
        self._concurrent = 200

    def unzip(self):
        with gzip.open(self.index_path, 'rb') as f_in:
            with open(self.json_file_name, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

    def get_network_files(self, state_name, plan_type):
        urls = []

        with open(self.json_file_name, 'r') as f:
            objects = ijson.items(
                f, 'reporting_structure.item.in_network_files.item')

            for obj in objects:
                print(obj.get('description'))
                if state_name in obj.get('description').lower() and plan_type in obj.get('description').lower():
                    urls.append(obj.get('location'))

        return urls

    def _unique_ein(self):
        ein = []
        with open(self.json_file_name, 'r') as f:
            objects = ijson.items(
                f, 'reporting_structure.item.reporting_plans.item')

            ein = [obj.get('plan_id') if obj['plan_id_type'] ==
                   'EIN' else None for obj in objects]
            ein = list(set(ein))
        # 142,885 unique ein
        return ein

    def parse_ein_file_lookup(self):
        ''' parses api call fro ein_file_lookup to retrieve all "in network files"
            returns a list of file urls
        '''

        pool = multiprocessing.pool.ThreadPool(processes=self._concurrent)
        return_list = pool.map(self.ein_file_lookup, self.unique_ein)
        pool.close()

        return return_list

    @staticmethod
    def ein_file_lookup(ein):
        url = 'https://antm-pt-prod-dataz-nogbd-nophi-us-east1.s3.amazonaws.com/anthem/{}.json'.format(
            ein)
        headers = {'Content-type': 'application/json'}

        try:
            response = requests.get(url, headers=headers)
            data = response.json()
            return [file["url"] for file in data['In-Network Negotiated Rates Files']]
        except:
            # TODO only catch request errors not all errors
            print("error with ein: {}".format(ein))


if __name__ == '__main__':
    ip = IndexParser('2023-02-01_anthem_index.json.gz')

    ip.unzip()
    url = ip.get_network_files(state_name='new york', plan_type='ppo')

    with open("new_york_ppo.txt", "w") as f:
        for item in url:
            f.write(str(item) + "\n")
