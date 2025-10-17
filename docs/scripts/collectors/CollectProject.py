from .CollectorBase import CollectorBase
from datetime import datetime, timedelta

class CollectProject(CollectorBase):
    def execute(self, data: dict, metrics: dict, members) -> dict:
        draftIssues = data['project']
        iterations_data = data['iterations']
        statuses_data = data['statuses']
        statuses = [s.strip().lower().replace(" ", "_") for s in statuses_data]
        iterations = {}
        has_iterations = False
        for iteration in iterations_data:
            has_iterations = True
            start_date_str = iteration['startDate']
            duration_days = iteration['duration'] 
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = start_date + timedelta(days=duration_days - 1)
            end_date_str = end_date.strftime("%Y-%m-%d")
            iterations[iteration['title']] = {
                "title" : iteration['title'],
                "startDate" : start_date_str,
                "endDate" : end_date_str,
                "duration" :duration_days
            }
        issues_by_iteration = {title: [] for title in iterations.keys()}
        issues_by_iteration["no_iteration"] = []
        for _, draftIssue in draftIssues.items():
            iteration = draftIssue['iteration']
            title = iteration if iteration else "no_iteration"
            issues_by_iteration[title].append(draftIssue)
        metrics_by_iteration = {}
        for iteration_title, issues in issues_by_iteration.items():
            assigned_draftIssue_per_member = {member: 0 for member in members}
            assigned_per_member_by_status = {status: {member: 0 for member in members} for status in statuses}
            non_assigned = 0
            total = 0
            total_by_status = {status: 0 for status in statuses}
            features_by_status = {status: 0 for status in statuses}
            total_issues = 0
            total_issues_with_type = 0
            total_features = 0
            total_tasks = 0
            total_bugs = 0
            for draftIssue in issues:
                total +=1
                status = draftIssue['status'].strip().lower().replace(" ", "_")
                if draftIssue['item_type'] == 'Issue':
                    total_issues +=1
                    if draftIssue['issue_type'] != None:
                        total_issues_with_type +=1
                        if draftIssue['issue_type'] == "Feature":
                            total_features += 1
                            if status in features_by_status:
                                features_by_status[status] += 1
                        elif draftIssue['issue_type'] == "Bug":
                            total_bugs +=1
                        elif draftIssue['issue_type'] == "Task":
                            total_tasks += 1
                            if status in total_by_status:
                                total_by_status[status] += 1
                            if draftIssue['assignee'] != None and draftIssue['assignee'] in members:
                                assigned_draftIssue_per_member[draftIssue['assignee']] +=1
                                if status in assigned_per_member_by_status:
                                    assigned_per_member_by_status[status][draftIssue['assignee']] += 1
                            else:
                                non_assigned += 1

            assigned_draftIssue_per_member['non_assigned'] = non_assigned
            per_status_keys = {
                f"{status}_per_member": counts
                for status, counts in assigned_per_member_by_status.items()
            }

            per_status_feature = {
                f"total_features_{status}": counts
                for status, counts in features_by_status.items()
        
            }

            metrics_by_iteration[iteration_title]= {
                "assigned_per_member": assigned_draftIssue_per_member,
                **per_status_keys,
                **total_by_status,
                "total_issues": total_issues,
                "total_issues_with_type": total_issues_with_type,
                "total_features":total_features,
                "total_tasks": total_tasks,
                "total_bugs" : total_bugs,
                **per_status_feature,
                "total": total
            }
        iterations = dict(
            sorted(
                iterations.items(),
                key=lambda item: datetime.strptime(item[1]['startDate'], "%Y-%m-%d")
            )
        )
        assigned_draftIssue_per_member = {member: 0 for member in members}
        assigned_per_member_by_status = {status: {member: 0 for member in members} for status in statuses}
        non_assigned = 0
        total = 0
        total_by_status = {status: 0 for status in statuses}
        features_by_status = {status: 0 for status in statuses}
        total_issues = 0
        total_issues_with_type = 0
        total_features = 0
        total_tasks = 0
        total_bugs = 0
        for _,draftIssue in draftIssues.items():
            total +=1
            status = draftIssue['status'].strip().lower().replace(" ", "_")
            if draftIssue['item_type'] == 'Issue':
                total_issues +=1
                if draftIssue['issue_type'] != None:
                    total_issues_with_type +=1
                    if draftIssue['issue_type'] == "Feature":
                        total_features += 1
                        if status in features_by_status:
                            features_by_status[status] += 1
                    elif draftIssue['issue_type'] == "Bug":
                        total_bugs +=1
                    elif draftIssue['issue_type'] == "Task":
                        total_tasks += 1
                        if status in total_by_status:
                            total_by_status[status] += 1
                        if draftIssue['assignee'] != None and draftIssue['assignee'] in members:
                            assigned_draftIssue_per_member[draftIssue['assignee']] +=1
                            if status in assigned_per_member_by_status:
                                assigned_per_member_by_status[status][draftIssue['assignee']] += 1
                        else:
                            non_assigned += 1
        assigned_draftIssue_per_member['non_assigned'] = non_assigned

        per_status_keys = {
            f"{status}_per_member": counts
                for status, counts in assigned_per_member_by_status.items()
        }

        per_status_feature = {
            f"total_features_{status}": counts
            for status, counts in features_by_status.items()
        }
        metrics_by_iteration["total"]= {
                "assigned_per_member": assigned_draftIssue_per_member,
                **per_status_keys,
                **total_by_status,
                "total_issues": total_issues,
                "total_issues_with_type": total_issues_with_type,
                "total_features":total_features,
                "total_tasks": total_tasks,
                "total_bugs" : total_bugs,
                **per_status_feature,
                "total": total
        }
        metrics['project'] = {
            'has_iterations': has_iterations,
            'iterations': iterations,
            'metrics_by_iteration': metrics_by_iteration
        }
        return metrics
         
