// Copyright (c) Hervé Bredin
// Distributed under the terms of the Modified BSD License.

import {
  DOMWidgetModel,
  DOMWidgetView,
  ISerializers,
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from './version';

import '../css/widget.css';


export class LabelsModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: LabelsModel.model_name,
      _model_module: LabelsModel.model_module,
      _model_module_version: LabelsModel.model_module_version,
      _view_name: LabelsModel.view_name,
      _view_module: LabelsModel.view_module,
      _view_module_version: LabelsModel.view_module_version,
    };
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers,
    // Add any extra serializers here
  };

  static model_name = 'LabelsModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'LabelsView';
  static view_module = MODULE_NAME;
  static view_module_version = MODULE_VERSION;
}

export class LabelsView extends DOMWidgetView {
  container: HTMLDivElement;

  render() {
    this.container = document.createElement('div');
    this.el.appendChild(this.container);

    this.labels_changed();
    this.model.on('change:labels', this.labels_changed, this);
    this.model.on('change:colors', this.labels_changed, this);
  }

  labels_changed() {
    var labels = this.model.get("labels");
    var colors = this.model.get("colors");
    this.container.textContent = "";
    for (const idx of Object.keys(labels)) {
      var button = document.createElement('button');
      button.textContent = "[" + idx + "] " + labels[idx];
      button.style.backgroundColor = colors[idx];
      this.container.appendChild(button);
    }
  }
}
