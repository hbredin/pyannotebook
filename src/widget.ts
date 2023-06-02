// MIT License
//
// Copyright (c) 2022- CNRS
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

import {
  DOMWidgetModel,
  DOMWidgetView,
  ISerializers,
} from '@jupyter-widgets/base';

import { MODULE_NAME, MODULE_VERSION } from './version';

import '../css/widget.css';

import WaveSurfer from 'wavesurfer.js';
import RegionsPlugin from 'wavesurfer.js/src/plugin/regions';
import MinimapPlugin from 'wavesurfer.js/src/plugin/minimap';

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
  private wavesurfer_minimap: HTMLDivElement;
  private _wavesurfer: WaveSurfer;
  private _adding_regions: boolean;
  private _syncing_regions: boolean;

  to_blob(b64: string) {
    // https://stackoverflow.com/questions/27980612/converting-base64-to-blob-in-javascript
    // https://ionic.io/blog/converting-a-base64-string-to-a-blob-in-javascript
    const byteString = atob(b64.split(',')[1]);
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);

    for (let i = 0; i < byteString.length; i++) {
      ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: 'audio/x-wav' });
  }

  render() {
    const plugins = [];

    const minimap = this.model.get('minimap');
    if (minimap) {
      this.wavesurfer_minimap = document.createElement('div');
      this.el.appendChild(this.wavesurfer_minimap);
      plugins.push(
        MinimapPlugin.create({
          container: this.wavesurfer_minimap,
          waveColor: '#777',
          progressColor: '#222',
          height: 20,
        })
      );
    }

    this.wavesurfer_container = document.createElement('div');
    this.el.appendChild(this.wavesurfer_container);
    plugins.push(
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
      })
    );

    this._wavesurfer = WaveSurfer.create({
      container: this.wavesurfer_container,
      barGap: 1,
      barHeight: 1,
      barRadius: 2,
      barWidth: 2,
      scrollParent: true,
      plugins: plugins,
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
    this._wavesurfer.on('zoom', this.on_zoom.bind(this));

    this._wavesurfer.on('ready', this.on_ready.bind(this));

    this.update_b64();
    this.model.on('change:b64', this.update_b64, this);
    this.model.on('change:colors', this.update_colors, this);

    this.model.on('change:playing', this.update_playing, this);
    this.model.on('change:time', this.update_time, this);
    this.model.on('change:zoom', this.update_zoom, this);

    this.model.on('change:regions', this.update_regions, this);
    this.model.on('change:active_region', this.update_active_region, this);

    this.model.on('change:overlap', this.update_overlap, this);
  }

  push_regions() {
    const regions = this._wavesurfer.regions.list;
    const region_ids = Object.keys(regions);
    const _regions = [];
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

  update_b64() {
    const b64 = this.model.get('b64');
    const blob = this.to_blob(b64);
    this._wavesurfer.clearRegions();
    this._wavesurfer.loadBlob(blob);
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
        attributes: { label: region.label },
      });
    }

    this._adding_regions = false;

    this.update_colors();
    this.update_active_region();
    this.update_overlap();
    this.update_label_visibility();
  }

  update_colors() {
    const regions = this.model.get('regions');
    const colors = this.model.get('colors');
    const wavesurfer_regions = this._wavesurfer.regions.list;
    for (const region of regions) {
      wavesurfer_regions[region['id']].element.style.backgroundColor =
        colors[region['label']];
    }
  }

  update_active_region() {
    const regions = this.model.get('regions');
    const active_region = this.model.get('active_region');
    const wavesurfer_regions = this._wavesurfer.regions.list;

    for (const region of regions) {
      if (region['id'] === active_region) {
        wavesurfer_regions[region['id']].element.classList.add(
          'wavesurfer-region-active'
        );
      } else {
        wavesurfer_regions[region['id']].element.classList.remove(
          'wavesurfer-region-active'
        );
      }
    }
  }

  update_overlap() {
    const regions = this.model.get('regions');
    const overlap = this.model.get('overlap');
    const wavesurfer_regions = this._wavesurfer.regions.list;

    for (const region of regions) {
      const wavesurfer_region = wavesurfer_regions[region['id']].element;

      for (const class_name of wavesurfer_region.className.split(' ')) {
        if (class_name.startsWith('wavesurfer-region-overlapping')) {
          wavesurfer_region.classList.remove(class_name);
        }
      }
      if (region.id in overlap) {
        wavesurfer_region.classList.add(
          'wavesurfer-region-overlapping-' +
            overlap[region.id].level +
            '-' +
            overlap[region.id].num_levels
        );
      }
    }
  }

  update_label_visibility() {
    const regions = this.model.get('regions');
    const wavesurfer_regions = this._wavesurfer.regions.list;

    for (const region of regions) {
      const wavesurfer_region = wavesurfer_regions[region['id']].element;
      const tag = wavesurfer_region.querySelector(
        '.wavesurfer-region-tag'
      ) as HTMLElement | null;

      if (tag !== null) {
        tag.style.display = 'inline';
        tag.style.display =
          tag.getBoundingClientRect().width >
          0.9 * wavesurfer_region.getBoundingClientRect().width
            ? 'none'
            : 'inline';
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

  update_zoom() {
    const zoom = this.model.get('zoom');
    this._wavesurfer.zoom(zoom);
    this.update_colors();
    this.update_label_visibility();
  }

  // FIXME: find correct type for `created_region`
  on_region_created(created_region: any) {
    let label;
    if ('label' in created_region.attributes) {
      label = created_region.attributes.label;
    } else {
      label = this.model.get('active_label');
      created_region.attributes.label = label;
    }

    const tag = document.createElement('span');
    tag.textContent = label.toUpperCase();
    tag.classList.add('wavesurfer-region-tag');

    const r = created_region.element;
    r.appendChild(tag);

    if (!this._adding_regions) {
      this.model.set('active_region', created_region.id);
      this.touch();
    }
  }

  // FIXME: find correct type for `created_region`
  on_region_update_end(updated_region: any) {
    const wavesurfer_regions = this._wavesurfer.regions.list;
    const region_ids = Object.keys(wavesurfer_regions);
    const regions = [];
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
    this.update_label_visibility();
  }

  on_audioprocess() {
    this.model.set('time', this._wavesurfer.getCurrentTime());
    this.touch();
  }

  on_seek(progress: number) {
    this.model.set('time', this._wavesurfer.getCurrentTime());
    this.touch();
  }

  on_zoom(minPxPerSec: number) {
    console.log('minPxPerSec', minPxPerSec);
    this.update_label_visibility();
  }

  on_finish() {
    this.model.set('playing', false);
    this.touch();
  }

  // FIXME: find correct type for `region`
  on_region_click(region: any) {
    let active_region;
    if (region.id === this.model.get('active_region')) {
      active_region = '';
    } else {
      active_region = region.id;
    }

    this.model.set('active_region', active_region);
    this.touch();
  }

  on_ready() {
    this.update_active_region();
    this.update_colors();
    this.update_overlap();
    this.update_label_visibility();
    this.update_playing();
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
    const labels = this.model.get('labels');
    const colors = this.model.get('colors');
    const active_label = this.model.get('active_label');

    this.container.textContent = '';
    for (const idx of Object.keys(labels)) {
      const button = document.createElement('button');
      button.style.backgroundColor = colors[idx];
      button.classList.add('label-button');
      if (idx === active_label) {
        button.classList.add('label-button-active');
      }

      const shortcut = document.createElement('span');
      shortcut.style.backgroundColor = 'white';
      shortcut.classList.add('label-shortcut');
      if (idx === active_label) {
        shortcut.classList.add('label-button-active');
      }
      shortcut.textContent = idx.toUpperCase();
      button.appendChild(shortcut);

      const label = document.createElement('input');
      label.classList.add('label-input');
      label.value = labels[idx];
      label.addEventListener('keypress', this.save_label_on_enter(label, idx));
      button.appendChild(label);
      button.addEventListener('click', this.activate(idx));
      this.container.appendChild(button);
    }
    const add_button = document.createElement('button');
    add_button.textContent = '+';
    add_button.classList.add('label-button');
    add_button.addEventListener('click', this.add_label());
    this.container.appendChild(add_button);
  }

  activate(idx: string) {
    return (event: any) => {
      this.model.set('active_label', idx);
      this.touch();
    };
  }

  save_label_on_enter(label: HTMLInputElement, idx: string) {
    return (event: any) => {
      if (event.key === 'Enter') {
        event.preventDefault();
        const new_labels = Object();
        const old_labels = this.model.get('labels');
        for (const i in old_labels) {
          if (i === idx) {
            new_labels[i] = label.value;
          } else {
            new_labels[i] = old_labels[i];
          }
        }
        this.model.set('labels', new_labels);
        this.touch();
      }
    };
  }
  add_label() {
    return (event: any) => {
      const new_labels = Object();
      const old_labels = this.model.get('labels');
      const old_colors = this.model.get('colors');
      const new_idx = Object.keys(old_labels).length;
      for (const i in old_labels) {
        new_labels[i] = old_labels[i];
      }
      new_labels[new_idx] = 'New Label';
      this.model.set('labels', new_labels);

      const new_colors = Object();
      for (const i in old_colors) {
        new_colors[i] = old_colors[i];
      }
      new_colors[new_idx] = '#000000';
      this.model.set('colors', new_colors);

      this.model.set('active_label', new_idx);
      this.touch();
    };
  }
}

// add front end of the control bar, based on the label exemple
export class ControlBarModel extends DOMWidgetModel {
  defaults() {
    return {
      ...super.defaults(),
      _model_name: ControlBarModel.model_name,
      _model_module: ControlBarModel.model_module,
      _model_module_version: ControlBarModel.model_module_version,
      _view_name: ControlBarModel.view_name,
      _view_module: ControlBarModel.view_module,
      _view_module_version: ControlBarModel.view_module_version,
    };
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers,
    // Add any extra serializers here
  };

  static model_name = 'ControlBarModel';
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = 'ControlBarView';
  static view_module = MODULE_NAME;
  static view_module_version = MODULE_VERSION;
}

export class ControlBarView extends DOMWidgetView {
  container: HTMLDivElement;

  render() {
    this.container = document.createElement('div');
    this.el.appendChild(this.container);

    this.update_control_bar();
    this.model.on('change:control_bar', this.update_control_bar, this);
  }

  update_control_bar() {
    //const control_play = this.model.get('play_command');
    const playing = this.model.get('playing');
    //const control_bar = this.model.get('control_bar');

    this.container.textContent = '';

    const play_control_bar = document.createElement('div');

    const fast_backward = document.createElement('button');
    fast_backward.classList.add('control-bar-button');
    fast_backward.textContent = '<<';
    fast_backward.addEventListener('click', this.fast_backward());
    play_control_bar.appendChild(fast_backward);

    const backward = document.createElement('button');
    backward.classList.add('control-bar-button');
    backward.textContent = '<';
    backward.addEventListener('click', this.backward());
    play_control_bar.appendChild(backward);

    const play = document.createElement('button');
    play.classList.add('control-bar-button');
    if (playing) {
      play.textContent = '||';
    } else {
      play.textContent = '->';
    }

    play.addEventListener('click', this.play());
    play_control_bar.appendChild(play);

    const forward = document.createElement('button');
    forward.classList.add('control-bar-button');
    forward.textContent = '>';
    forward.addEventListener('click', this.forward());
    play_control_bar.appendChild(forward);

    const fast_forward = document.createElement('button');
    fast_forward.classList.add('control-bar-button');
    fast_forward.textContent = '>>';
    fast_forward.addEventListener('click', this.fast_forward());
    play_control_bar.appendChild(fast_forward);
    play_control_bar.classList.add('sub-control-bar');
    this.container.appendChild(play_control_bar);

    const zoom_control_bar = document.createElement('div');

    const zoom_in = document.createElement('button');
    zoom_in.classList.add('control-bar-button');
    zoom_in.textContent = '+';
    zoom_in.addEventListener('click', this.zoom_in());
    zoom_control_bar.appendChild(zoom_in);

    const zoom_out = document.createElement('button');
    zoom_out.classList.add('control-bar-button');
    zoom_out.textContent = '-';
    zoom_out.addEventListener('click', this.zoom_out());
    zoom_control_bar.appendChild(zoom_out);
    zoom_control_bar.classList.add('sub-control-bar');
    this.container.appendChild(zoom_control_bar);

    const region_control_bar = document.createElement('div');

    const insert_region = document.createElement('button');
    insert_region.classList.add('control-bar-button');
    insert_region.textContent = 'Insert Region';
    insert_region.addEventListener('click', this.insert_region());
    region_control_bar.appendChild(insert_region);

    const cut_region = document.createElement('button');
    cut_region.classList.add('control-bar-button');
    cut_region.textContent = 'Cut Region';
    cut_region.addEventListener('click', this.cut_region());
    region_control_bar.appendChild(cut_region);

    const delete_region = document.createElement('button');
    delete_region.classList.add('control-bar-button');
    delete_region.textContent = 'Delete Region';
    delete_region.addEventListener('click', this.delete_region());

    region_control_bar.appendChild(delete_region);
    region_control_bar.classList.add('sub-control-bar');

    this.container.classList.add('control-bar');

    this.container.appendChild(region_control_bar);
  }

  fast_backward() {
    return (event: any) => {
      this.model.set('play_command', 'fast_backward');
      this.touch();
      this.model.set('play_command', 'none');
      this.touch();
    };
  }

  backward() {
    return (event: any) => {
      this.model.set('play_command', 'backward');
      this.touch();
      this.model.set('play_command', 'none');
      this.touch();
    };
  }

  play() {
    return (event: any) => {
      this.model.set('play_command', 'play');
      this.model.set('playing', !this.model.get('playing'));
      this.model.set('play_command', 'none');
      this.touch();
    };
  }

  forward() {
    return (event: any) => {
      this.model.set('play_command', 'forward');
      this.touch();
      this.model.set('play_command', 'none');
      this.touch();
    };
  }

  fast_forward() {
    return (event: any) => {
      this.model.set('play_command', 'fast_forward');
      this.touch();
      this.model.set('play_command', 'none');
      this.touch();
    };
  }

  zoom_in() {
    return (event: any) => {
      this.model.set('control_bar', 'zoom_in');
      this.touch();
    };
  }

  zoom_out() {
    return (event: any) => {
      this.model.set('control_bar', 'zoom_out');
      this.touch();
    };
  }

  insert_region() {
    return (event: any) => {
      this.model.set('control_bar', 'insert_region');
      this.touch();
    };
  }

  cut_region() {
    return (event: any) => {
      this.model.set('control_bar', 'cut_region');
      this.touch();
    };
  }

  delete_region() {
    return (event: any) => {
      this.model.set('control_bar', 'delete_region');
      this.touch();
    };
  }
}
