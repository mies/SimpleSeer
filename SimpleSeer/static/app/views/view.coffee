require 'lib/view_helper'

# Base class for all views.
module.exports = class View extends Backbone.View
  subviews: null

  initialize: =>
    @subviews = {}

  template: =>
    return

  getRenderData: =>
    return

  render: =>
    # console.debug "Rendering #{@constructor.name}"
    @$el.html @template @getRenderData()
    @renderSubviews()
    @afterRender()
    this

  afterRender: =>
    return

  renderSubviews: =>
    for name, subview of @subviews
      subview.render()

  addSubview: (name, viewClass, selector, options) =>
    options = options or {}
    _.extend options,
      parent:@
      selector:selector
    @subviews[name] = new viewClass(options)
