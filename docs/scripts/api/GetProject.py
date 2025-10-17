from .APInterface import APInterface
import requests

class GetProject(APInterface):
    def execute(self, owner_name, repo_name, headers, project_number, data: dict) -> dict:
        if project_number <= 0: 
            data['project'] = {
            }
            data["iterations"] = []
            data["statuses"] = []
            return data
        url = "https://api.github.com/graphql"
        cursor = None
        project = {}
        while True:
            query = """
            {
                organization(login: "%s") {
                    projectV2(number: %d) {
                        title
                        fields(first: 100) {
                            nodes {
                                ... on ProjectV2IterationField {
                                    id
                                    name
                                    configuration {
                                        iterations {
                                                id
                                                title
                                                startDate                                                
                                                duration
                                            
                                        }
                                    }
                                }
                                ... on ProjectV2SingleSelectField {
                                    name
                                    options {
                                        name
                                    }
                                }
                            }
                        }
                        items(first: 100%s) {
                            nodes {
                                content {
                                    __typename
                                    ... on Issue {
                                        title
                                        id
                                        issueType  {
                                            name
                                        }
                                        assignees(first: 1) {
                                            nodes {
                                                login
                                            }
                                        }
                                    }
                                    ... on DraftIssue {
                                        title
                                        id
                                        assignees(first: 1) {
                                            nodes {
                                                login
                                            }
                                        }
                                    }
                                }
                                fieldValues(first: 10) {
                                    nodes {
                                        ... on ProjectV2ItemFieldSingleSelectValue {
                                            field {
                                                ... on ProjectV2FieldCommon {
                                                    name
                                                }
                                            }
                                            name
                                        }
                                          ... on ProjectV2ItemFieldIterationValue {
                                                id
                                                title
                                                startDate
                                                duration
                                        }
                                    }
                                }
                            }
                            pageInfo {
                                hasNextPage
                                endCursor
                            }
                        }
                    }
                }
            }
            """ % (owner_name, project_number, f', after: "{cursor}"' if cursor else "")


            response = requests.post(url, json={'query': query}, headers=headers)
            if response.status_code != 200:
                raise requests.RequestException(f"Error al fer la trucada a {self.__class__.__name__}: {response.status_code}")
            
            data_graphql = response.json()
            iterations_list = []
            statuses_list = []
            if 'data' in data_graphql:
                iteration_Data = data_graphql['data']['organization']['projectV2']['fields']['nodes']
                items_data = data_graphql['data']['organization']['projectV2']['items']['nodes']
                page_info = data_graphql['data']['organization']['projectV2']['items']['pageInfo']
                for field in iteration_Data:
                    if field.get('name') == 'Iteration' and 'configuration' in field:
                        for iteration in field.get('configuration', {}).get('iterations', []):
                            iterations_list.append({
                                'id': iteration.get('id'),
                                'title': iteration.get('title'),
                                'startDate': iteration.get('startDate'),
                                'duration': iteration.get('duration'),
                            })
                    elif field.get('name') == 'Status':
                        status_options = field.get('options', [])
                        statuses_list = [opt['name'] for opt in status_options]

                for item in items_data:
                    id = None
                    title = None
                    assignees = None
                    status = None
                    item_type = None
                    issue_type = None

                    if 'content' in item:
                        content = item['content']
                        if 'id' in content:
                            id = content['id']
                        if 'title' in content:
                            title = content['title']
                        if 'assignees' in content:
                            assignees = content['assignees']['nodes']
                            assignee = assignees[0]['login'] if assignees else None
                        if  '__typename' in content:
                            item_type = content['__typename']
                        if item_type == "Issue" and 'issueType' in content and content['issueType']:
                                issue_type = content['issueType']['name']
                        iteration_title = None
                        for field_value in item['fieldValues']['nodes']:
                            if 'field' in field_value and field_value['field']['name'] == "Status":
                                status = field_value['name']
                            elif all(k in field_value for k in ['id', 'title', 'startDate', 'duration']):
                                iteration_title = field_value['title']
                                if not any(it['title'] == iteration_title for it in iterations_list):
                                    iterations_list.append({
                                        'id': field_value['id'],
                                        'title': iteration_title,
                                        'startDate': field_value['startDate'],
                                        'duration': field_value['duration']
                                    })
                    if id and item_type != "Issue": 
                        project[id] = {
                            "title": title,
                            "assignee": assignee,
                            "status": status,
                            "item_type": item_type,
                            "iteration":iteration_title,
                        }
                    elif id and item_type == "Issue":
                        project[id] = {
                            "title": title,
                            "assignee": assignee,
                            "status": status,
                            "item_type": item_type,
                            "iteration":iteration_title,
                            "issue_type" : issue_type
                        }
                    
                if page_info['hasNextPage']:
                    cursor = page_info['endCursor']
                else:
                    break
            else:
                break
        if "project" in data:
            data["project"].update(project)
        else:
            data["project"] = project

        if "iterations" in data:
            data["iterations"].update(iterations_list)
        else:
             data["iterations"] = iterations_list
        if "statuses" in data:
            data["statuses"].update(statuses_list)
        else:
             data["statuses"] = statuses_list
        return data
