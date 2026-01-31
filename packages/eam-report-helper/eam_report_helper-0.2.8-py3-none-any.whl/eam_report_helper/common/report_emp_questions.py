

class EmpQuestionsReport:
    def __init__(self, db, company_id: str) -> None:
        self.db = db
        self.companyId = company_id

    def format_questions(self, emp_questions: list) -> list:
        """Format questions"""
        results = []
        for item in emp_questions:
            if self.companyId in [x['id'] for x in item['employerList']]:
                results.append(item)

        return results

    def format_answers(self, vendor_list_items: list, vend_answers: list, emp_questions_formatted: list, emp_questions: list) -> list:
        """Format answers"""
        vendor_ids = [x['vendorId'] for x in vendor_list_items]
        emp_question_ids = [x['id'] for x in emp_questions_formatted]

        results = []
        for item in vend_answers:
            if (item['vendorId'] in vendor_ids) and (item['empQuestionId'] in emp_question_ids):
                item['inputType'] = [x['inputType']
                                     for x in emp_questions if x['id'] == item['empQuestionId']][0]
                item['questionText'] = [x['text']
                                        for x in emp_questions if x['id'] == item['empQuestionId']][0]
                results.append(item)

        return results

    def format_answers_by_question_type(self, vend_answers_formatted: list) -> list:
        """Format answers by question type"""
        for item in vend_answers_formatted:
            if item['inputType'] == 'mult_select':
                item['answer'] = str([x['text'] for x in item['answer'] if x['isActive'] is True]).replace(
                    '[', '').replace(']', '').replace('\'', '')

        return vend_answers_formatted

    def build_emp_questions_report(self) -> dict:
        """Build Tundra employee questions report"""
        vendor_list_items = self.db.get_results(
            query=f"SELECT c.vendorId, c.vendorName, c.employerId, c.employerName FROM c WHERE c.type = 'vendorList' AND c.employerId = '{self.companyId}'")

        emp_questions = self.db.get_results(
            query=f"SELECT * FROM c WHERE c.type = 'empQuestion'")

        emp_questions_formatted = self.format_questions(emp_questions)

        vend_answers = self.db.get_results(
            query=f"SELECT * FROM c WHERE c.type = 'vendAnswer'")

        vend_answers_formatted = self.format_answers(
            vendor_list_items, vend_answers, emp_questions_formatted, emp_questions)

        vend_answers_by_type = self.format_answers_by_question_type(
            vend_answers_formatted)

        rows = []
        for vendor_id in list(set([x['vendorId'] for x in vendor_list_items])):
            row_object = {'Vendor Name': [
                x['vendorName'] for x in vendor_list_items if x['vendorId'] == vendor_id][0]}
            for inner_item in vend_answers_by_type:
                if vendor_id == inner_item['vendorId']:
                    row_object[inner_item['questionText']
                               ] = inner_item['answer']

            if len(row_object) > 1:
                rows.append(row_object)

        return {
            'file_name': 'Questions_Report.csv',
            'headers': ['Vendor Name'] + [x['text'] for x in emp_questions_formatted],
            'rows': rows
        }
