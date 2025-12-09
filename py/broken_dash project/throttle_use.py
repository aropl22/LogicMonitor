# Get dashboards for a group
throttle()
dashboards = api_instance.get_dashboard_list(filter=f"groupId:{group_id}", size=1000).items

# Get each dashboard config
for dashboard in dashboards:
    throttle()
    dashboard_detail = api_instance.get_dashboard_by_id(dashboard.id)

    widgets_config = dashboard_detail.to_dict().get("widgets_config", {})
    for w_id in widgets_config.keys():
        throttle()
        widget_detail = api_instance.get_widget_by_id(w_id)
