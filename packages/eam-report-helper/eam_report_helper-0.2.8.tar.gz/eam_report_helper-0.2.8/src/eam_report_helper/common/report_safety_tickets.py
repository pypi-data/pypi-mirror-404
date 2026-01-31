from datetime import datetime
import os


class SafetyTicketsReport:
    """Safety Tickets Report"""

    def __init__(self, db, company_id: str, b2c_helper) -> None:
        self.db = db
        self.company_id = company_id
        self.b2c_helper = b2c_helper

    def get_report_headers(self) -> list:
        """Get report headers"""

        docs = self.db.get_results(
            query="SELECT * FROM c WHERE c.type = 'doc' AND c.docClass = 'additionalRequirement' AND c.isUserTicket = true")

        results = []
        for doc in docs:
            if 'employerId' in doc:
                if doc['employerId'] == self.company_id:
                    results.append(
                        {'docType': doc['docType'], 'docRef': doc['docRef']})
                else:
                    pass
            else:
                results.append(
                    {'docType': doc['docType'], 'docRef': doc['docRef']})

        return results

    def remove_duplicates(self, active_docs: list):
        """Remove duplicates"""
        test = []
        for item in active_docs:
            for key in item.keys():
                test.append(key)

        distinct_list = list(set(test))

        test = []
        for item in active_docs:
            for inner in distinct_list:
                for key, val in item.items():
                    if key == inner:

                        item = {
                            'key': key,
                            'val': val
                        }

                        try:
                            item['val'] = datetime.strptime(val, '%Y-%m-%d')
                        except ValueError:
                            pass

                        test.append(item)

        filtered_list = [x for x in test if x['val'] != '']

        final = []
        for item in distinct_list:
            try:
                tested = datetime.strftime(
                    max([x['val'] for x in filtered_list if x['key'] == item]), '%Y-%m-%d')
                final.append({item: tested})
            except ValueError:
                final.append({item: ''})

        return final

    def prime(self, base_dict: dict, user_doc_questions: list, user_doc_ids_by_user: list):
        """Prime"""
        user_doc_questions = [
            x for x in user_doc_questions if x['userDocId'] in user_doc_ids_by_user]

        test = []
        for k, v in enumerate(base_dict.items()):
            for item in user_doc_questions:
                if (k > 1) and (item['docRef'] == v[1]['docRef']):
                    test.append(
                        ({f"{v[1]['docType']} {item['text']}": item['answer']}))

        return test

    def build_final(self, user_docs: list, header_list: list):
        """Build final"""
        results = []
        for item in header_list:
            results.append({'key': item, 'val': ''})
            for inner in user_docs:

                for k, v in inner.items():
                    if item == k:
                        results.append({'key': k, 'val': v})

        final_results = []
        test = list(set(x['key'] for x in results))
        for item in test:
            tested = [x['val'] for x in results if x['key'] == item]

            if len(tested) > 1:
                final_results.append({
                    item: tested[1]
                })

            else:
                final_results.append({
                    item: ''
                })

        return final_results

    def build_safety_ticket_report(self, branch_id: str) -> dict:
        """Build safety ticket report"""
        headers = self.get_report_headers()

        b2c_users = self.b2c_helper.get_users(
            self.company_id, role_type=None, branch_id=branch_id)

        users = [
            x for x in b2c_users if x[f'extension_{os.environ["B2C_EXTENSION_APP_CLIENT_ID"]}_UserRoles'] != '8amAdmin']

        user_docs = self.db.get_results(
            query=f"SELECT * FROM c WHERE c.type = 'userDoc' and ARRAY_CONTAINS({[x['id'] for x in users]}, c.userId)")

        user_doc_questions = self.db.get_results(
            query=f"SELECT * FROM c WHERE c.type = 'userDocQuestion' and ARRAY_CONTAINS({[x['id'] for x in user_docs]}, c.userDocId)")

        doc_questions = self.db.get_results(
            query=f"SELECT * FROM c WHERE c.type = 'docQuestion'")

        new_headers = []
        for item in headers:
            for inner in doc_questions:
                if item['docRef'] == inner['docRef']:
                    new_headers.append(f"{item['docType']} {inner['text']}")

        new_headers = list(set(new_headers))

        user_rows = []
        for user in users:
            user_doc_ids_by_user = [x['id']
                                    for x in user_docs if user['id'] == x['userId']]

            test = {**{'User Name': user['displayName'],
                    'User Id': user['id']}, **dict(list(enumerate(headers)))}

            test = self.prime(test, user_doc_questions, user_doc_ids_by_user)

            if test:
                docs = self.remove_duplicates(test)
                row = self.build_final(docs, new_headers)
                row[0] = {
                    'User Name': user['displayName']
                }
                result = {}
                for obj in row:
                    result.update(obj)
                user_rows.append(result)

        return {
            'file_name': 'Safety_Tickets_Report.csv',
            'headers': ['User Name'] + new_headers,
            'rows': user_rows
        }
