from datetime import datetime, timedelta

from .utils import Toggl


class TogglDefaultHookset(object):

    def update_project_line_item_times(self, api_key, project_to_update):
        if not project_to_update.categories.all().exists():
            return

        toggl = Toggl()
        toggl.setAPIKey(api_key)

        # We want to get a detailed report (list of line items)
        # for our project. That said, we don't know its id
        # and toggl doesn't have an option to list all projects.
        # It does however let you get projects for a particular
        # client so we'll grab all the clients and get a project
        # list that way.
        clients = toggl.getClients()
        toggl_projects = []
        for client in clients:
            clients_projects = toggl.getClientProjects(client['id'])
            if clients_projects:
                toggl_projects += clients_projects

        # Right now we are assuming that every project has a unique name
        # Note: Toggl requires a workspace id to get a detailed report
        # so we need to grab the one associated with the project
        project_id = None
        workspace_id = None
        for project in toggl_projects:
            if project['name'] == project_to_update.name:
                project_id = project['id']
                workspace_id = project['wid']
                break
        if project_id is None:
            return

        # Get tags that correspond to our categories
        all_tags = toggl.getTags()
        project_to_update_categories = project_to_update.categories.all()
        category_names = {category.name for category
                          in project_to_update_categories}
        ids_for_tags_that_match_categories = []
        for tag in all_tags:
            if tag['name'] in category_names:
                ids_for_tags_that_match_categories.append(tag['id'])

        # Grab all line items tagged with our categories
        # for our project over the last year.
        one_year_ago = datetime.now() - timedelta(weeks=52)
        toggl_report_criteria = {
            'project_ids': [project_id],
            'since': one_year_ago.strftime('%Y-%m-%d'),
            'tag_ids': ids_for_tags_that_match_categories,
            'without_description': 'false',
            'workspace_id': workspace_id,
        }
        toggl_report = toggl.getDetailedReport(data=toggl_report_criteria)

        items_per_page = int(toggl_report['per_page'])
        page = 2
        toggl_line_items = toggl_report['data']
        total_items = int(toggl_report['total_count'])
        total_pages = total_items/items_per_page
        while page < total_pages:
            toggl_report_criteria['page'] = page
            toggl_report = toggl.getDetailedReport(data=toggl_report_criteria)
            toggl_line_items += toggl_report['data']
            page += 1

        # Add up the durations for all of the line items
        # whose descriptions match the descriptions of our
        # project's line items.
        project_to_update_line_items = []
        for category in project_to_update_categories:
            line_items = category.items.all()
            if line_items.exists():
                project_to_update_line_items += list(line_items)
        if not project_to_update_line_items:
            return

        line_items_by_description = {item.description : item
                                     for item in project_to_update_line_items}
        line_item_totals = {item.description: 0
                            for item in project_to_update_line_items}

        for line_item in toggl_line_items:
            if line_item['description'] in line_item_totals:
                total = line_item_totals[line_item['description']]
                total+= line_item['dur'] / (1000 * 60 * 60)
                line_item_totals[line_item['description']] = total
                # toggl returns duration in milliseconds

        for description, total in line_item_totals.items():
            line_item = line_items_by_description[description]
            line_item.actual = total
            line_item.save()


class HookProxy(object):

    def __getattr__(self, attr):
        return getattr(TogglDefaultHookset, attr)


hookset = HookProxy()