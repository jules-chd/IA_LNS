import plotly.graph_objects as go
import json


def load_json(file_path):
    with open(file_path) as f:
        return json.load(f)


def get_facility_utilization(instance, solution):
    no_facilities = len(instance['facilities'])
    facility_utilization = [0 for facility in range(no_facilities)]
    for customer, demand in enumerate(instance['customer_demands']):
        customer_facility = solution[customer]
        facility_utilization[customer_facility] += demand
    return facility_utilization


def prepare_heatmap_trace(instance):
    no_facilities = len(instance['facilities'])
    no_customers = len(instance['customer_demands'])
    assignment_cost_matrix = [[None for customer in range(no_customers)] for facility in range(no_facilities)]
    for facility in range(no_facilities):
        for customer in range(no_customers):
            assignment_cost_matrix[facility][customer] = instance['assignment_costs'][facility][customer]
    heatmap_trace = go.Heatmap(z=assignment_cost_matrix, colorscale="Greys", showscale=False)
    return heatmap_trace


def prepare_highlight_trace(solution):
    cells_to_highlight = [(facility, customer) for customer, facility in enumerate(solution)]
    highlight_trace = go.Scatter(
        x=[c for (f, c) in cells_to_highlight],
        y=[f for (f, c) in cells_to_highlight],
        mode="markers",
        marker=dict(symbol="square", size=50, color="rgba(0,0,0,0)", line=dict(color="red", width=5)),
        showlegend=False
    )
    return highlight_trace


def prepare_customer_annotations(instance):
    return [
        dict(
            x=customer_id, y=-2.5,
            text=f'C{customer_id} demand {demand}',
            showarrow=False, font=dict(color="black", size=14), textangle=270
        )
        for customer_id, demand in enumerate(instance['customer_demands'])
    ]


def prepare_facility_left_annotations(instance, solution):
    facility_utilization = get_facility_utilization(instance, solution)
    return [
        dict(
            x=-2.5, y=facility_id,
            text=f'F{facility_id} opening cost {facility["opening_cost"]}', showarrow=False,
            font=dict(color="black" if facility_utilization[facility_id] > 0 else "grey", size=14), textangle=0
        )
        for facility_id, facility in enumerate(instance['facilities'])
    ]


def prepare_facility_right_annotations(instance, solution):
    no_customers = len(instance['customer_demands'])
    facility_utilization = get_facility_utilization(instance, solution)
    return [
        dict(
            x=no_customers + 2.5, y=facility_id,
            text=f'Capacity used: {facility_utilization[facility_id]}/{facility["capacity"]}', showarrow=False,
            font=dict(color="black" if facility_utilization[facility_id] > 0 else "grey", size=14), textangle=0
        )
        for facility_id, facility in enumerate(instance['facilities'])
    ]


def visualize_solution(instance_path, solution_path):
    instance, solution = load_json(instance_path), load_json(solution_path)
    no_facilities, no_customers = len(instance['facilities']), len(instance['customer_demands'])

    heatmap_trace = prepare_heatmap_trace(instance)
    highlight_trace = prepare_highlight_trace(solution)

    fig = go.Figure()
    fig.update_layout(
        width=60 * no_customers, height=70 * no_facilities,
        xaxis=dict(range=(-5.5, no_customers + 5.5), showticklabels=False, ticks="", showgrid=False),
        yaxis=dict(range=(-5.5, no_facilities + 0.5), showticklabels=False, ticks="", showgrid=False)
    )

    fig.add_trace(highlight_trace)
    fig.add_trace(heatmap_trace)

    customer_annotations = prepare_customer_annotations(instance)
    facility_left_annotations = prepare_facility_left_annotations(instance, solution)
    facility_right_annotations = prepare_facility_right_annotations(instance, solution)
    annotations = customer_annotations + facility_left_annotations + facility_right_annotations

    fig.update_layout(
        annotations=annotations,
        margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False
    )
    fig.show()


