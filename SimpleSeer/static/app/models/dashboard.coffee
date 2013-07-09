Model = require "./model"
application = require 'application'
dashboardWidget = require 'views/core/dashboardWidget'

module.exports = class Dashboard extends Model
  urlRoot: "/api/dashboard"
  loaded: false

  @schema:
    type: 'Object'
    id:
      type: 'String'
      required: true
      help: "Dashboard Object ID as generated by MongoDB"
    name:
      type: 'String'
      required: true
      help: "Human readable name for the dashboard"
    locked:
      type: 'Boolean'
      required: true
      default: true
      help: "Lock/unlock user's ability to edit the dashboard"
    cols:
      type: 'Int'
      required: true
      default: 1
      help: "How many grid columns the dashboard spans"
    rowHeight:
      type: 'Int'
      required: false
      default: 100
      help: "How many vertical pixels the dashboard spans"
    widgets:
      type: 'Array'
      required: false
      item:
        type: 'Object'
        id:
          type: 'String'
          required: true
          help: "Widget Object ID as generated by MongoDB"
        name:
          type: 'String'
          required: true
          help: "Human readable name for the widget"
        canAlter:
          type: 'Boolean'
          required: true
          default: true
          help: "Allow/disallow user's ability to alter the widget"
        model:
          type: 'String'
          required: false
          default: 'null'
          help: "Backbone model the widget inherits"
        view:
          type: 'String'
          required: true
          help: "Backbone view the widget inherits"
        cols:
          type: 'Int'
          required: true
          default: 1
          help: "How many grid columns the widget spans"
        help: "A widget item"
        extras: false
      help: "A list of widgets that the dashboard contains"
    help: "Dashboard's contain a list of widgets"
    extras: true

  initialize: =>
    if @attributes.view
      @view = @attributes.view
      delete @attributes.view
    super()


  loadElements: =>
    if @view
      @view.clearSubviews()
      for widget in @attributes.widgets
        vi = @view.addSubview "widget_"+widget.id, dashboardWidget, @view.$el.find("#widget_grid").get(), {append:"widget_"+widget.id,widget:widget}
        vi.render()
      @loaded = true

