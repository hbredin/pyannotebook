// Copyright (c) Hervé Bredin
// Distributed under the terms of the Modified BSD License.

import {
  DOMWidgetModel,
  DOMWidgetView,
  ISerializers,
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from './version';

import '../css/widget.css';

import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/src/plugin/regions';

export class WavesurferModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: WavesurferModel.model_name,
      _model_module: WavesurferModel.model_module,
      _model_module_version: WavesurferModel.model_module_version,
      _view_name: WavesurferModel.view_name,
      _view_module: WavesurferModel.view_module,
      _view_module_version: WavesurferModel.view_module_version,
    };
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers,
    // Add any extra serializers here
  };

  static model_name = 'WavesurferModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'WavesurferView';
  static view_module = MODULE_NAME;
  static view_module_version = MODULE_VERSION;
}

export class WavesurferView extends DOMWidgetView {
  private wavesurfer_container: HTMLDivElement;
  private _wavesurfer: WaveSurfer;
  private _adding_regions: boolean;
  private _syncing_regions: boolean;

  to_blob(b64: string) {
    // https://stackoverflow.com/questions/27980612/converting-base64-to-blob-in-javascript
    // https://ionic.io/blog/converting-a-base64-string-to-a-blob-in-javascript
    var byteString = atob(b64.split(',')[1]);
    var ab = new ArrayBuffer(byteString.length);
    var ia = new Uint8Array(ab);

    for (var i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: 'audio/x-wav' });
  }

  render() {
    this.wavesurfer_container = document.createElement('div');
    this.el.appendChild(this.wavesurfer_container);

    this._wavesurfer = WaveSurfer.create({
      container: this.wavesurfer_container,
      scrollParent: true,
      plugins: [
        RegionsPlugin.create({
          regionsMinLength: 0,
          /** Enable creating regions by dragging with the mouse. */
          dragSelection: true,
          /** Regions that should be added upon initialisation. */
          regions: undefined,
          /** The sensitivity of the mouse dragging (default: 2). */
          slop: 2,
          /** Snap the regions to a grid of the specified multiples in seconds? */
          snapToGridInterval: undefined,
          /** Shift the snap-to-grid by the specified seconds. May also be negative. */
          snapToGridOffset: undefined,
          /** Maximum number of regions that may be created by the user at one time. */
          maxRegions: undefined,
          /** Allows custom formating for region tooltip. */
          formatTimeCallback: undefined,
          /** from container edges' Optional width for edgeScroll to start (default: 5% of viewport width). */
          edgeScrollWidth: undefined,
        }),
      ],
    });

    this._wavesurfer.on(
      'region-update-end',
      this.on_region_update_end.bind(this)
    );
    this._wavesurfer.on('region-created', this.on_region_created.bind(this));
    this._wavesurfer.on('audioprocess', this.on_audioprocess.bind(this));
    this._wavesurfer.on('seek', this.on_seek.bind(this));
    this._wavesurfer.on('finish', this.on_finish.bind(this));
    this._wavesurfer.on('region-click', this.on_region_click.bind(this));

    this.update_audio();
    this.model.on('change:audio', this.update_audio, this);
    this.model.on('change:regions', this.update_regions, this);
    this.model.on('change:colors', this.update_colors, this);
    this.model.on('change:overlap', this.update_overlap, this);
    this.model.on('change:playing', this.update_playing, this);
    this.model.on('change:time', this.update_time, this);
    this.model.on(
      'change:active_region',
      this.update_active_region,
      this
    );
  }

  push_regions() {
    const regions = this._wavesurfer.regions.list;
    const region_ids = Object.keys(regions);
    var _regions = [];
    for (const region_id of region_ids) {
      const region = regions[region_id];
      _regions.push({
        start: region.start,
        end: region.end,
        id: region_id,
        label: region.attributes.label,
      });
    }

    this._syncing_regions = true;
    this.model.set('regions', _regions);
    this.touch();
    this._syncing_regions = false;
  }

  update_audio() {
    var blob = this.to_blob(this.model.get('audio'));
    this._wavesurfer.loadBlob(blob);
    this._wavesurfer.clearRegions();
  }

  update_regions() {

    if (this._syncing_regions) {
      return;
    }

    const regions = this.model.get('regions');

    this._adding_regions = true;

    this._wavesurfer.clearRegions();
    for (const region of regions) {
      this._wavesurfer.addRegion({
        start: region.start,
        end: region.end,
        id: region.id,
        attributes: {"label": region.label},
      });      
    }

    this._adding_regions = false;

    this.update_colors();
    this.update_active_region();
    this.update_overlap();
  }

  update_colors() {
    const regions = this.model.get('regions');
    const colors = this.model.get('colors');
    const wavesurfer_regions = this._wavesurfer.regions.list;
    
    for (const region of regions) {
      wavesurfer_regions[region["id"]].element.style.backgroundColor = colors[region["label"]];
    }
  }

  update_active_region() {
    const regions = this.model.get('regions');
    const active_region = this.model.get('active_region');
    const wavesurfer_regions = this._wavesurfer.regions.list;

    for (const region of regions) {
      if (region["id"] == active_region) {
        wavesurfer_regions[region["id"]].element.classList.add('wavesurfer-region-active');
      } 
      else {
        wavesurfer_regions[region["id"]].element.classList.remove('wavesurfer-region-active');
      }
    }
  }

  update_overlap() {
    const regions = this.model.get('regions');
    const overlap = this.model.get('overlap');
    const wavesurfer_regions = this._wavesurfer.regions.list;

    for (const region of regions) {
      var wavesurfer_region = wavesurfer_regions[region["id"]].element;

      for (const class_name of wavesurfer_region.className.split(' ')) {
        if (class_name.startsWith("wavesurfer-region-overlapping")) {
          wavesurfer_region.classList.remove(class_name);
        }
      }
      if (region.id in overlap) {
        wavesurfer_region.classList.add('wavesurfer-region-overlapping-' + overlap[region.id].level + '-' + overlap[region.id].num_levels);
      }
    }
  }

  update_playing() {
    if (this.model.get('playing')) {
      this._wavesurfer.play();
    } else {
      this._wavesurfer.pause();
    }
  }

  update_time() {
    if (!this.model.get('playing')) {
      this._wavesurfer.setCurrentTime(this.model.get('time'));
    }
  }


  // FIXME: find correct type for `created_region`
  on_region_created(created_region: any) {
    var label;
    if ('label' in created_region.attributes) {
      label = created_region.attributes.label;
    } else {
      label = this.model.get('active_label');
      created_region.attributes.label = label;
    }

    var l = created_region.element.appendChild(document.createElement('span'));
    l.textContent = label;

    if (!this._adding_regions) {
      this.model.set('active_region', created_region.id);
      this.touch();
    }
  }

  // FIXME: find correct type for `created_region`
  on_region_update_end(updated_region: any) {
    const wavesurfer_regions = this._wavesurfer.regions.list;
    const region_ids = Object.keys(wavesurfer_regions);
    var regions = [];
    for (const region_id of region_ids) {
      const region = wavesurfer_regions[region_id];
      regions.push({
        start: region.start,
        end: region.end,
        id: region_id,
        label: region.attributes.label,
      });
    }

    this._syncing_regions = true;
    this.model.set('regions', regions);
    this.touch();
    this._syncing_regions = false;

    this.update_active_region();
    this.update_colors();
    this.update_overlap();
  }

  on_audioprocess() {
    this.model.set('time', this._wavesurfer.getCurrentTime());
    this.touch();
  }

  on_seek(progress: number) {
    this.model.set('time', this._wavesurfer.getCurrentTime());
    this.touch();
  }

  on_finish() {
    this.model.set('playing', false);
    this.touch();
  }

  // FIXME: find correct type for `region`
  on_region_click(region: any) {
    var active_region;
    if (region.id == this.model.get('active_region')) {
      active_region = "";
    } else {
      active_region = region.id;
    }

    this.model.set('active_region', active_region);
    this.touch();
  }
}


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

    this.update_labels();
    this.model.on('change:labels', this.update_labels, this);
    this.model.on('change:colors', this.update_labels, this);
    this.model.on('change:active_label', this.update_labels, this);
  }

  update_labels() {
    var labels = this.model.get("labels");
    var colors = this.model.get("colors");
    var active_label = this.model.get("active_label");

    this.container.textContent = "";
    for (const idx of Object.keys(labels)) {

      var button = document.createElement('button');
      button.style.backgroundColor = colors[idx];
      button.classList.add('label-button');

      var shortcut = document.createElement('span');
      shortcut.style.backgroundColor = "white";
      shortcut.classList.add('label-shortcut');

      if (idx == active_label) {
        button.classList.add('label-button-active');
        shortcut.classList.add('label-button-active');
      }

      var i = parseInt(idx);
      if (i < 10) {
        shortcut.textContent = idx;
      } else {
        if (i < 20) {
          shortcut.innerHTML = "&#8679;" + (i % 10);
        }
      }
      button.appendChild(shortcut);

      var label = document.createElement('span');
      label.textContent = labels[idx];
      button.appendChild(label);
      button.addEventListener("click", this.activate(idx)); 
      this.container.appendChild(button);
    }
  }

  activate(idx: string) {
    var that = this;
    return function(event: any) {
      that.model.set('active_label', parseInt(idx));
      that.touch();
    };
  };

}
