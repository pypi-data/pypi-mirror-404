import pkg_resources


class FormReportHelper:
    """Form Report Helper"""

    def __init__(self, database, b2c_helper):
        self.database = database
        self.b2c_helper = b2c_helper

    def get_item_by_template(self, v: dict, elements: list) -> str:
        """Get the item by label"""

        element: dict = [
            x for x in elements if x['id'] == v['elementId']][0]
        try:
            v['value'] = [x['label']
                          for x in element['options'] if x['value'] == v['value']][0]
        except IndexError:
            pass

        return v['value']

    def get_item_by_label(self, v: dict, users: list, template: dict) -> str:
        """Get the item by label"""

        try:
            row_item = v['value']

            if v['type'] == 'inpSelectUser':

                if 'displayName' in v['value']:
                    row_item = [x['displayName']
                                for x in users if x['id'] == v['value']['id']][0]
                if 'first' in v['value']:
                    row_item = f"{v['value']['first']} {v['value']['last']}"

                else:
                    row_item = ''

            if v['type'] == 'inpSelect':
                row_item = self.get_item_by_template(
                    v, template['elements'])

            if v['type'] == 'inpAssignUser':
                row_item = f"{v['value']['first']} {v['value']['last']}"

        except KeyError:
            row_item = v['values']
        except IndexError:

            # ELEMENT ID FOR ASSIGN SUPERVISOR
            if v['elementId'] == 'b13b95f4-39a1-4712-bf40-7d41e0f17cce':
                row_item = f"{v['value']['first']} {v['value']['last']}"
            else:
                row_item = v['value']

        return row_item

    def match_elements(self, distribution: dict, template: dict, users: list, sub_forms: list = None) -> dict:
        """Match the elements"""

        row = {
            'Form Name': distribution['template']['name'],
        }

        if 'sequenceNumber' in distribution:
            row['Report Number'] = distribution['sequenceNumber']

        for k, v in distribution['data'].items():

            if ('value' in v) or ('values' in v):

                try:
                    label = [x['label'] for x in template['elements']
                             if x['id'] == v['elementId']][0]

                    row[label] = self.get_item_by_label(v, users, template)

                except IndexError:
                    pass

        # Combine the sub form data with the form data
        if sub_forms is not None:
            for sub_form in sub_forms:
                if distribution['id'] == sub_form['distribution_id']:
                    row = {**row, **sub_form['matched_elements']}

        return row

    def build_asignee(self, sub_form: dict) -> str:

        try:
            if 'first' and 'last' in sub_form['matched_elements']['Corrective Action Responsibility']:
                return f"{sub_form['matched_elements']['Corrective Action Responsibility']['first']} {sub_form['matched_elements']['Corrective Action Responsibility']['last']}"

            else:
                return sub_form['matched_elements']['Corrective Action Responsibility']
        except KeyError:
            return ""

        except TypeError:
            return ""

    def get_sub_forms(self, distributions: list, users: list) -> list:
        """Get the sub forms"""

        sub_form_ref_list = []
        # Match form with subform
        for distribution in distributions:
            for k, v in distribution['data'].items():
                for key, value in v.items():
                    if key == 'subForm':
                        for item in value:
                            sub_form_ref_list.append({
                                'distribution_id': distribution['id'],
                                'sub_form_distribution_id': item['id']
                            })

        # Get the sub form distributions
        sub_forms = self.database.get_results(
            query=f"SELECT * FROM c where c.type = 'formDistribution' and ARRAY_CONTAINS({[x['sub_form_distribution_id'] for x in sub_form_ref_list]}, c.id)")

        for ref in sub_form_ref_list:
            for sub_form in sub_forms:
                if ref['sub_form_distribution_id'] == sub_form['id']:
                    ref['sub_form_template_id'] = sub_form['template']['id']
                    ref['sub_form'] = sub_form

        sub_form_ref_list_filtered = [
            x for x in sub_form_ref_list if 'sub_form_template_id' in x]

        templates = self.database.get_results(
            query=f"SELECT * FROM c where c.type = 'formTemplate' and ARRAY_CONTAINS({[x['sub_form_template_id'] for x in sub_form_ref_list_filtered]}, c.id)")

        for sub_form in sub_form_ref_list_filtered:
            if 'sub_form_template_id' in sub_form:
                for template in templates:
                    if sub_form['sub_form_template_id'] == template['id']:
                        sub_form['sub_form_template'] = template

        # Match the sub form distribution items with the template
        for sub_form in sub_form_ref_list_filtered:
            matched_elements = self.match_elements(sub_form['sub_form'],
                                                   sub_form['sub_form_template'], users, None)
            matched_elements['Status'] = sub_form['sub_form']['status']
            sub_form['matched_elements'] = matched_elements

        # Get the sub form elements in proper order, this will only work for Corrective Action?
        for sub_form in sub_form_ref_list_filtered:
            sub_form['matched_elements'].pop('Form Name')
            sub_form['matched_elements'] = dict({
                'Corrective Action Description': sub_form['matched_elements']['Corrective Action Description'],
                'Corrective Action Status': sub_form['matched_elements']['Status'],
                'Corrective Action Asignee': self.build_asignee(sub_form),
                'Corrective Action Target Date': sub_form['matched_elements']['Corrective Action Due Date'],
                'Corrective Action Completion Date': sub_form['matched_elements']['Corrective Action Completion Date'],
            })

        return sub_form_ref_list_filtered

    def remove_empty_columns(self, column_names: list, rows: list):
        """Remove empty columns"""

        for column_name in column_names:
            try:
                if all(row[column_name] == '' for row in rows):
                    for row in rows:
                        del row[column_name]
                if all(row[column_name] == [] for row in rows):
                    for row in rows:
                        del row[column_name]
            except KeyError:
                pass

        all_keys = [key for row in rows for key in row.keys()]

        return {'column_names': list(dict.fromkeys(all_keys)), 'rows': rows}

    def format_cell_lists(self, rows: list) -> list:
        """for all rows, if the value is a list, join the list into a string"""
        new_rows = []
        for row in rows:
            for key, value in row.items():
                if isinstance(value, list):
                    for i, v in enumerate(value):
                        if isinstance(v, list):
                            value[i] = ' - '.join(v)

                    row[key] = '\n'.join(value)

        return rows

    def get_form_report(self, template_id: str,  report_name: str, branch_id: str) -> dict:
        """Get the Insignia Hazard ID History"""
        template = self.database.get_result(
            query=f"SELECT * FROM c where c.type = 'formTemplate' and c.id = '{template_id}'")

        distributions = self.database.get_results(
            query=f"SELECT * FROM c where c.type = 'formDistribution' and c.template.id = '{template_id}' ORDER BY c.sequenceNumber DESC")

        users = self.b2c_helper.get_users(
            company_id=template['companyId'],
            role_type=None,
            branch_id=branch_id
        )

        sub_forms = self.get_sub_forms(distributions, users)

        rows = []
        for distribution in distributions:
            rows.append(self.match_elements(
                distribution, template, users, sub_forms))

        ordinal_list = []

        for item in template['elements']:
            ordinal_list.append(item)

        if len(sub_forms) > 0:
            column_names = [x['label'] for x in ordinal_list] + \
                [x for x in sub_forms[0]['matched_elements'].keys()]
        else:
            column_names = [x['label'] for x in ordinal_list]

        formatted_rows: dict = self.format_cell_lists(rows)
        formatted_rows: dict = self.remove_empty_columns(column_names, rows)

        return {
            'file_name': report_name,
            'headers': formatted_rows['column_names'],
            'rows': formatted_rows['rows']
        }
