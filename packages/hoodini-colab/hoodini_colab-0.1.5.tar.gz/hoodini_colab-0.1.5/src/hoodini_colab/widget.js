function render({ model, el }) {
    el.style.width = '100%';
    el.style.display = 'block';

    // --- STATE MANAGEMENT ---
    let currentMode = 'single'; // single, list, sheet
    
    const params = {
        'Input/Output': [
            { name: 'input', type: 'text', label: 'Input', desc: 'Protein ID, FASTA, or file path', modes: ['single', 'list'] },
            { name: 'output', type: 'text', label: 'Output Folder', desc: 'Output folder name', def: 'results' },
            { name: 'force', type: 'switch', label: 'Force Overwrite', desc: 'Force re-download and overwrite existing files', def: false },
            { name: 'mount-gdrive', type: 'switch', label: 'Mount Google Drive', desc: 'Mount Google Drive and save results to My Drive', def: false, colab_only: true },
            
        ],
        'Remote BLAST': [
            { name: 'remote-evalue', type: 'float', label: 'E-value', desc: 'Remote BLAST E-value', modes: ['single'], def: 1e-5 },
            { name: 'remote-max-targets', type: 'int', label: 'Max Targets', desc: 'Max targets to retrieve', modes: ['single'], def: 100 }
        ],
        'Neighborhood Window': [
            { name: 'win-mode', type: 'select', label: 'Window Mode', desc: 'Window mode', options: ['win_nts', 'win_genes'], def: 'win_nts' },
            { name: 'win', type: 'int', label: 'Window Size', desc: 'Window size', def: 20000 },
            { name: 'min-win', type: 'int', label: 'Min Window', desc: 'Min window size', def: 2000 },
            { name: 'min-win-type', type: 'select', label: 'Min Window Type', desc: 'Type of min window', options: ['total', 'upstream', 'downstream', 'both'], def: 'both' }
        ],
        'Clustering': [
            { name: 'cand-mode', type: 'select', label: 'Candidate Mode', desc: 'IPG representative mode', options: ['any_ipg', 'best_ipg', 'best_id', 'one_id', 'same_id'], def: 'best_id' },
            { name: 'clust-method', type: 'select', label: 'Clustering Method', desc: 'Clustering method', options: ['diamond_deepclust', 'deepmmseqs', 'jackhmmer', 'blastp'], def: 'diamond_deepclust' }
        ],
        'Tree Construction': [
            { name: 'tree-mode', type: 'select', label: 'Tree Mode', desc: 'Tree building method', options: ['taxonomy', 'fast_nj', 'aai_tree', 'ani_tree', 'fast_ml', 'neigh_similarity_tree', 'neigh_phylo_tree'], def: 'fast_ml' }
        ],
        'Pairwise Comparisons': [
            { name: 'ani-mode', type: 'select', label: 'ANI Mode', desc: 'ANI calculation method', options: ['fastani', 'skani', 'blastn'], def: 'fastani' },
            { name: 'nt-aln-mode', type: 'select', label: 'NT Alignment', desc: 'Nucleotide alignment mode', options: ['blastn', 'fastani', 'minimap2', 'intergenic_blastn'], def: 'blastn' },
            { name: 'aai-mode', type: 'select', label: 'AAI Mode', desc: 'AAI/proteome similarity mode', options: ['aai', 'wgrr'], def: 'wgrr' },
            { name: 'aai-subset-mode', type: 'select', label: 'AAI Subset', desc: 'AAI subset mode', options: ['target_prot', 'target_region', 'window'], def: 'target_region' },
            { name: 'min-pident', type: 'float', label: 'Min % Identity', desc: 'Min percent identity', def: 30.0 }
        ],
        'Annotations': [
            { name: 'padloc', type: 'bool', label: 'PADLOC', desc: 'Antiphage defense' },
            { name: 'deffinder', type: 'bool', label: 'DefenseFinder', desc: 'Antiphage defense' },
            { name: 'cctyper', type: 'bool', label: 'CCtyper', desc: 'CRISPR-Cas prediction' },
            { name: 'ncrna', type: 'text', label: 'ncRNA (RFAM)', desc: 'Comma-separated RFAM IDs (e.g., RF00001,RF02348)', placeholder: 'RF00001,RF02348' },
            { name: 'genomad', type: 'bool', label: 'geNomad', desc: 'MGE identification' },
            { name: 'sorfs', type: 'bool', label: 'sORFs', desc: 'Reannotate small open reading frames' },
            { name: 'emapper', type: 'bool', label: 'eggNOG-mapper', desc: 'Run eggNOG-mapper to annotate proteins' },
            { name: 'domains', type: 'multiselect', label: 'Domains', desc: 'MetaCerberus DBs', 
              options: ['amrfinder', 'cazy', 'cog', 'foam', 'gvdb', 'kegg', 'kofam', 'methmmdb', 'nfixdb', 'pfam', 'pgap', 'phrog', 'pvog', 'tigrfam', 'vog-r225'] }
        ],
        'Links': [
            { name: 'prot-links', type: 'switch', label: 'Protein Links', desc: 'Pairwise protein comparisons', def: false },
            { name: 'nt-links', type: 'switch', label: 'Nucleotide Links', desc: 'Pairwise nucleotide comparisons', def: false }
        ]
    };

    const state = {};
    const multiSelectState = {}; // For multiselect values
    const sheetData = []; // Table data for inputsheet mode
    const sheetColumns = ['protein_id', 'nucleotide_id', 'start', 'end', 'strand', 'uniprot_id', 'assembly_id'];
    let sheetTable = null; // Tabulator instance
    
    Object.values(params).flat().forEach(p => {
        if (p.type === 'multiselect') multiSelectState[p.name] = [];
    });

    // Using simple HTML table instead of external library

    // --- DEBUG PANEL ---

    const categoryStyles = {
        'Remote BLAST': { bg: '#ede9fe', text: '#6d28d9' },
        'Input/Output': { bg: '#e0e7ff', text: '#4338ca' },
        'Neighborhood Window': { bg: '#fef3c7', text: '#b45309' },
        'Clustering': { bg: '#fce7f3', text: '#be185d' },
        'Tree Construction': { bg: '#ccfbf1', text: '#0f766e' },
        'Pairwise Comparisons': { bg: '#ffedd5', text: '#c2410c' },
        'Annotations': { bg: '#f3f4f6', text: '#374151' },
        'Links': { bg: '#f3f4f6', text: '#374151' }
    };

    // Icons
    const icons = {
        chevronDown: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>',
        chevronRight: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 18l6-6-6-6"/></svg>',
        copy: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>',
        play: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
        refresh: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M23 4v6h-6"/><path d="M1 20v-6h6"/><path d="M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>',
        check: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>',
        alert: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
        terminal: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>',
        dna: '<svg width="24" height="24" viewBox="0 0 145.7 150.8" fill="currentColor"><circle cx="43.2" cy="29.7" r="13.1"/><circle cx="104.7" cy="30.7" r="13.1"/><path d="M68.9,49.4c-0.1,14-7.7,30.3-27.5,30.2S14.3,63,14.3,49.1s7.6-30.3,27.5-30.2S69,35.4,68.9,49.4z M60.3,49.4 c0-10.7-4.9-22.9-18.5-23S22.9,38.4,22.9,49.1s4.9,22.9,18.6,23S60.1,60.1,60.3,49.4z"/><path d="M132,49.9c-0.1,14-7.7,30.3-27.5,30.2S77.3,63.5,77.4,49.5s7.6-30.3,27.5-30.2S132.1,35.9,132,49.9z M123.3,49.8c0.1-10.7-4.8-22.9-18.5-23C91.2,26.8,86,38.9,85.9,49.6s4.9,22.9,18.6,23S123.3,60.5,123.3,49.8z"/><path d="M60.6,61.8l10,20.5c0.8,1.6,3.5,1.7,4.3,0l9.2-21c0.6-1.2,0.3-2.6-0.9-3.4c-1.2-0.7-2.7-0.3-3.4,0.9l-9.2,21 h4.3l-10-20.6c-0.7-1.2-2.2-1.6-3.4-0.9C60.4,59.1,60,60.6,60.6,61.8L60.6,61.8z"/><polygon points="121.1,84.1 113.3,84.1 113.3,122.1 74.4,122.1 74.4,115 99.6,115 99.6,84.1 91.6,84.1 91.6,107 44.7,107 44.7,102.9 56.1,102.9 56.1,84.1 47.9,84.1 47.9,94.7 32,94.7 32,84.1 23.7,84.1 23.7,102.9 36.7,102.9 36.7,115 66.5,115 66.5,130 92.4,130 92.4,150.8 100.4,150.8 100.4,130 121.1,130"/><path d="M60,33.2h9.9c-0.7-6-4-11.3-9-14.7c-5.6-4-12.6-5.1-19.4-5.2C35,13.1,28.3,14,21.8,12.7 C16.3,11.5,10,7.9,9.8,1.5c0-0.5-0.1-1-0.3-1.5H0.3C0.1,0.5,0,1,0,1.5c0.1,6.8,3.7,12.5,9.2,16.4c5.6,4,12.6,5.1,19.4,5.3 c6.5,0.2,13.2-0.7,19.7,0.6C53.2,24.9,58.9,27.9,60,33.2z"/><path d="M145.4,0h-9.3c-0.2,0.5-0.3,1-0.3,1.5c0,5.7-5.4,9.4-10.4,10.8c-6.9,1.9-14.2,0.8-21.2,1 c-6.7,0.2-13.8,1.3-19.4,5.2c-5,3.4-8.3,8.7-9,14.7h10c1-4.7,5.6-7.8,10.1-9c6.9-1.8,14.2-0.8,21.2-1c6.7-0.2,13.8-1.3,19.4-5.3 c5.4-3.9,9.1-9.6,9.2-16.4C145.6,1,145.5,0.5,145.4,0z"/></svg>',
        colab: '<svg width="24" height="24" viewBox="0 0 24 24" preserveAspectRatio="xMidYMid meet" focusable="false"><g><path d="M4.54,9.46,2.19,7.1a6.93,6.93,0,0,0,0,9.79l2.36-2.36A3.59,3.59,0,0,1,4.54,9.46Z" fill="#E8710A"></path><path d="M2.19,7.1,4.54,9.46a3.59,3.59,0,0,1,5.08,0l1.71-2.93h0l-.1-.08h0A6.93,6.93,0,0,0,2.19,7.1Z" fill="#F9AB00"></path><path d="M11.34,17.46h0L9.62,14.54a3.59,3.59,0,0,1-5.08,0L2.19,16.9a6.93,6.93,0,0,0,9,.65l.11-.09" fill="#F9AB00"></path><path d="M12,7.1a6.93,6.93,0,0,0,0,9.79l2.36-2.36a3.59,3.59,0,1,1,5.08-5.08L21.81,7.1A6.93,6.93,0,0,0,12,7.1Z" fill="#F9AB00"></path><path d="M21.81,7.1,19.46,9.46a3.59,3.59,0,0,1-5.08,5.08L12,16.9A6.93,6.93,0,0,0,21.81,7.1Z" fill="#E8710A"></path></g></svg>',
        x: '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
        plus: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>',
        trash: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg>',
        spinner: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="spinner-icon"><path d="M21 12a9 9 0 11-6.219-8.56"/></svg>'
    };
    // --- LOGIC ---

    function buildCommand() {
        let cmd = 'hoodini run';
        
        // Handle inputsheet mode specially
        if (currentMode === 'sheet' && sheetData.length > 0) {
            // Convert sheetData to TSV format
            const tsvLines = [sheetColumns.join('\\t')];
            sheetData.forEach(row => {
                const values = sheetColumns.map(col => row[col] || '');
                tsvLines.push(values.join('\\t'));
            });
            // For now, indicate that a sheet file would be generated
            cmd += ' --inputsheet <input_sheet.tsv>';
        }
        
        // Handle input list mode specially - send list data to Python
        if (currentMode === 'list' && state.input) {
            // Send the input list to Python so it can save it to a file
            model.set('input_list', state.input);
            model.save_changes();
        } else {
            // Clear input_list if not in list mode
            model.set('input_list', '');
            model.save_changes();
        }
        
        Object.values(params).flat().forEach(param => {
            if (param.modes && !param.modes.includes(currentMode)) return;
            
            // Skip inputsheet param in sheet mode (handled above)
            if (currentMode === 'sheet' && param.name === 'inputsheet') return;
            
            // Skip mount-gdrive as it's not a hoodini parameter
            if (param.name === 'mount-gdrive') return;
            
            let key = param.name;
            let value = state[key];
            
            // Handle multiselect
            if (param.type === 'multiselect') {
                const selected = multiSelectState[key] || [];
                if (selected.length > 0) {
                    cmd += ' --' + key + ' ' + selected.join(',');
                }
                return;
            }
            
            // Only include if explicitly set by user (not from default)
            if (value === undefined || value === '' || value === null) return;
            
            if (typeof value === 'boolean') {
                if (value) cmd += ' --' + key;
            } else {
                // In list mode, show placeholder since file will be created by Python
                if (key === 'input' && currentMode === 'list') {
                    cmd += ' --' + key + ' <input_list.txt>';
                } else {
                    let valStr = (typeof value === 'string' && value.includes(' ')) ? '"' + value + '"' : value;
                    cmd += ' --' + key + ' ' + valStr;
                }
            }
        });
        // Enforce Google Colab default threads: always use 2 and hide control
        cmd += ' --num-threads 2';
        return cmd;
    }

    function updateCommand() {
        const cmdEl = el.querySelector('.command-output');
        if (cmdEl) {
            const cmd = buildCommand();
            cmdEl.textContent = cmd;
            model.set('command', cmd);
            
            // Sync MetaCerberus databases selection
            const selectedDbs = multiSelectState['domains'] || [];
            model.set('metacerberus_dbs', selectedDbs.join(','));
            
            model.save_changes();
        }
        updateStatus();
    }

    function updateStatus() {
        const badge = el.querySelector('.status-badge');
        const runBtn = el.querySelector('#run-btn');
        
        if (badge) {
            let ready = false;
            if (currentMode === 'single' || currentMode === 'list') {
                ready = !!state.input;
            } else if (currentMode === 'sheet') {
                ready = sheetData.length > 0;
            }

            if (ready) {
                badge.className = 'status-badge status-ready';
                badge.innerHTML = icons.check + ' Ready';
                if (runBtn) runBtn.disabled = false;
            } else {
                badge.className = 'status-badge status-missing';
                badge.innerHTML = icons.alert + ' Input required';
                if (runBtn) runBtn.disabled = true;
            }
        }
    }

    function updateVisibility() {
        const items = el.querySelectorAll('.param-item[data-modes]');
        items.forEach(item => {
            const allowedModes = item.getAttribute('data-modes').split(',');
            if (allowedModes.includes(currentMode)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
        
        // Re-render input field if it's the input parameter (to switch between text and textarea)
        const inputParam = params['Input/Output'].find(p => p.name === 'input');
        if (inputParam) {
            const inputContainer = el.querySelector('.param-item[data-modes]');
            if (inputContainer && (currentMode === 'single' || currentMode === 'list')) {
                // Update description
                const descEl = inputContainer.querySelector('.param-desc');
                if (descEl) {
                    descEl.textContent = currentMode === 'list' 
                        ? 'List of NCBI/Uniprot protein IDs, or NCBI Nucleotide IDs'
                        : 'NCBI protein ID';
                }
                
                // Find the actual input element
                const oldInput = inputContainer.querySelector('.param-input, .param-textarea');
                if (oldInput) {
                    let newInput;
                    if (currentMode === 'list') {
                        newInput = document.createElement('textarea');
                        newInput.className = 'param-textarea';
                        newInput.rows = 6;
                        newInput.placeholder = 'Paste list of IDs (one per line)';
                    } else {
                        newInput = document.createElement('input');
                        newInput.className = 'param-input';
                        newInput.type = 'text';
                        newInput.placeholder = 'Enter NCBI protein ID';
                    }
                    newInput.value = state.input || '';
                    newInput.onchange = function() {
                        state.input = newInput.value || undefined;
                        if (!newInput.value) delete state.input;
                        updateCommand();
                    };
                    oldInput.parentNode.replaceChild(newInput, oldInput);
                }
            }
        }
        
        const remoteCat = el.querySelector('.category-section[data-category="Remote BLAST"]');
        if (remoteCat) {
            remoteCat.style.display = (currentMode === 'single') ? 'block' : 'none';
        }

        const sheetTable = el.querySelector('.sheet-table-container');
        if (sheetTable) {
            const show = (currentMode === 'sheet');
            sheetTable.style.display = show ? 'block' : 'none';
            if (show) renderSheetTable();
        }

        updateCommand();
    }

    function createSwitch(param) {
        const container = document.createElement('div');
        container.className = 'switch-container';
        
        const label = document.createElement('span');
        label.className = 'switch-label';
        label.innerText = param.label;
        
        const toggleWrapper = document.createElement('label');
        toggleWrapper.className = 'switch-wrapper';
        
        const input = document.createElement('input');
        input.type = 'checkbox';
        input.checked = (state[param.name] !== undefined) ? state[param.name] : !!param.def;
        input.onchange = () => {
            state[param.name] = input.checked;
            
            // Special handling for mount-gdrive: update output folder automatically
            if (param.name === 'mount-gdrive') {
                // Sync with Python model
                model.set('mount_gdrive', input.checked);
                model.save_changes();
                
                const outputInput = el.querySelector('input[placeholder*="Output folder"]');
                if (outputInput) {
                    if (input.checked) {
                        // Save current output value before changing
                        if (!state['output'] || state['output'] === 'results') {
                            state['_previous_output'] = 'results';
                        } else {
                            state['_previous_output'] = state['output'];
                        }
                        // Set to Google Drive path
                        state['output'] = '/content/drive/MyDrive';
                        outputInput.value = '/content/drive/MyDrive';
                    } else {
                        // Restore previous output value
                        const previousOutput = state['_previous_output'] || 'results';
                        state['output'] = previousOutput;
                        outputInput.value = previousOutput;
                        delete state['_previous_output'];
                    }
                }
            }
            
            updateCommand();
        };
        
        const slider = document.createElement('span');
        slider.className = 'switch-slider';
        
        toggleWrapper.appendChild(input);
        toggleWrapper.appendChild(slider);
        
        container.appendChild(label);
        container.appendChild(toggleWrapper);
        
        return container;
    }

    function createMultiSelect(param) {
        const container = document.createElement('div');
        container.className = 'multiselect-container';
        
        const labelEl = document.createElement('div');
        labelEl.className = 'multiselect-label';
        labelEl.innerText = param.label;
        container.appendChild(labelEl);
        
        const descEl = document.createElement('div');
        descEl.className = 'multiselect-desc';
        descEl.innerText = param.desc;
        container.appendChild(descEl);
        
        // Selected tags
        const tagsContainer = document.createElement('div');
        tagsContainer.className = 'multiselect-tags';
        container.appendChild(tagsContainer);
        
        // Dropdown
        const dropdown = document.createElement('div');
        dropdown.className = 'multiselect-dropdown';
        
        param.options.forEach(opt => {
            const optEl = document.createElement('div');
            optEl.className = 'multiselect-option';
            optEl.textContent = opt;
            optEl.onclick = () => {
                if (!multiSelectState[param.name].includes(opt)) {
                    multiSelectState[param.name].push(opt);
                    renderTags();
                    updateCommand();
                }
            };
            dropdown.appendChild(optEl);
        });
        container.appendChild(dropdown);
        
        function renderTags() {
            tagsContainer.innerHTML = '';
            multiSelectState[param.name].forEach(val => {
                const tag = document.createElement('span');
                tag.className = 'multiselect-tag';
                tag.innerHTML = val + ' <span class="tag-remove">' + icons.x + '</span>';
                tag.querySelector('.tag-remove').onclick = (e) => {
                    e.stopPropagation();
                    multiSelectState[param.name] = multiSelectState[param.name].filter(v => v !== val);
                    renderTags();
                    updateCommand();
                };
                tagsContainer.appendChild(tag);
            });
            
            if (multiSelectState[param.name].length === 0) {
                const placeholder = document.createElement('span');
                placeholder.className = 'multiselect-placeholder';
                placeholder.textContent = 'Click to select databases...';
                tagsContainer.appendChild(placeholder);
            }
        }
        
        tagsContainer.onclick = () => {
            dropdown.classList.toggle('show');
        };
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!container.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });
        
        renderTags();
        return container;
    }

    function createInput(param) {
        const container = document.createElement('div');
        container.className = 'param-item';
        if (param.modes) {
            container.setAttribute('data-modes', param.modes.join(','));
        }

        if (param.type === 'switch') {
            const switchEl = createSwitch(param);
            container.appendChild(switchEl);
            const desc = document.createElement('div');
            desc.className = 'param-desc';
            desc.textContent = param.desc;
            container.appendChild(desc);
            return container;
        }

        if (param.type === 'bool') {
            const label = document.createElement('label');
            label.className = 'param-checkbox';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.className = 'checkbox-input';
            checkbox.checked = state[param.name] || false;
            checkbox.onchange = function() {
                state[param.name] = checkbox.checked;
                updateCommand();
            };
            const text = document.createElement('span');
            text.innerHTML = '<strong>' + param.label + '</strong> <code class="param-flag">--' + param.name + '</code>';
            label.appendChild(checkbox);
            label.appendChild(text);
            container.appendChild(label);
            const desc = document.createElement('div');
            desc.className = 'param-desc';
            desc.textContent = param.desc;
            desc.style.marginLeft = '26px';
            container.appendChild(desc);
        } else {
            const labelEl = document.createElement('div');
            labelEl.className = 'param-label';
            labelEl.innerHTML = param.label + ' <code class="param-flag">--' + param.name + '</code>';
            container.appendChild(labelEl);
            const descEl = document.createElement('div');
            descEl.className = 'param-desc';
            descEl.textContent = param.desc;
            container.appendChild(descEl);
            
            let input;
            if (param.type === 'select') {
                input = document.createElement('select');
                input.className = 'param-input';
                const emptyOpt = document.createElement('option');
                emptyOpt.value = '';
                emptyOpt.textContent = '-- Select --';
                input.appendChild(emptyOpt);
                param.options.forEach(opt => {
                    const option = document.createElement('option');
                    option.value = opt;
                    option.textContent = opt;
                    if (state[param.name] === opt) option.selected = true;
                    input.appendChild(option);
                });
                if (state[param.name] === undefined && param.def !== undefined) {
                    input.value = param.def;
                }
            } else {
                // Special handling for input field in list mode - use textarea
                if (param.name === 'input' && currentMode === 'list') {
                    input = document.createElement('textarea');
                    input.className = 'param-textarea';
                    input.rows = 6;
                    input.placeholder = 'Paste list of IDs (one per line)';
                    if (state[param.name] !== undefined) input.value = state[param.name];
                } else {
                    input = document.createElement('input');
                    input.className = 'param-input';
                    input.type = (param.type === 'int' || param.type === 'float') ? 'number' : 'text';
                    if (param.type === 'float') input.step = '0.001';
                    input.placeholder = param.placeholder || (param.def !== undefined ? 'Default: ' + param.def : 'Enter ' + param.label.toLowerCase());
                    if (state[param.name] !== undefined) {
                        input.value = state[param.name];
                    } else if (param.def !== undefined) {
                        input.value = param.def;
                    }
                }
            }
            input.onchange = function() {
                const val = input.value;
                if (val === '') delete state[param.name];
                else if (param.type === 'int') state[param.name] = parseInt(val);
                else if (param.type === 'float') state[param.name] = parseFloat(val);
                else state[param.name] = val;
                updateCommand();
            };
            container.appendChild(input);
        }
        return container;
    }

    function addSheetRow(data = {}) {
        const row = {};
        sheetColumns.forEach(col => {
            row[col] = data[col] || '';
        });
        sheetData.push(row);
        if (sheetTable) {
            sheetTable.addRow(row);
        }
    }

    function removeSheetRow(index) {
        if (sheetTable) {
            const rows = sheetTable.getRows();
            if (rows[index]) {
                rows[index].delete();
            }
        }
        sheetData.splice(index, 1);
        updateCommand();
    }
    
    // --- SHEET TABLE FUNCTIONS ---
    function renderSheetTableUI() {
        console.log('[Sheet] Rendering simple HTML table');
        const tableHost = el.querySelector('#sheet-table');
        if (!tableHost) {
            console.error('[Sheet] Table host not found');
            return;
        }
        
        // Clear existing content
        tableHost.innerHTML = '';
        
        // Create table
        const table = document.createElement('table');
        table.className = 'sheet-simple-table';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.className = 'sheet-header-row';
        
        sheetColumns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            th.className = 'sheet-header-cell';
            headerRow.appendChild(th);
        });
        
        // Add delete column header
        const thDelete = document.createElement('th');
        thDelete.textContent = '';
        thDelete.className = 'sheet-header-cell sheet-delete-col';
        headerRow.appendChild(thDelete);
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        sheetData.forEach((row, rowIdx) => {
            const tr = document.createElement('tr');
            tr.className = 'sheet-data-row';
            tr.setAttribute('data-row-idx', rowIdx);
            
            sheetColumns.forEach(col => {
                const td = document.createElement('td');
                td.className = 'sheet-data-cell';
                td.setAttribute('data-col', col);
                td.textContent = row[col] || '';
                td.contentEditable = true;
                
                td.onblur = () => {
                    const newVal = td.textContent.trim();
                    if (sheetData[rowIdx]) {
                        sheetData[rowIdx][col] = newVal;
                        updateCommand();
                        console.log('[Sheet] Updated cell [' + rowIdx + '][' + col + ']');
                    }
                };
                
                tr.appendChild(td);
            });
            
            // Add delete button
            const tdDelete = document.createElement('td');
            tdDelete.className = 'sheet-delete-col';
            const btnDelete = document.createElement('button');
            btnDelete.className = 'sheet-delete-btn';
            btnDelete.innerHTML = icons.trash;
            btnDelete.onclick = (e) => {
                e.stopPropagation();
                deleteSheetRow(rowIdx);
            };
            tdDelete.appendChild(btnDelete);
            tr.appendChild(tdDelete);
            
            tbody.appendChild(tr);
        });
        table.appendChild(tbody);
        
        tableHost.appendChild(table);
        console.log('[Sheet] Table rendered with ' + sheetData.length + ' rows');
    }
    
    function deleteSheetRow(rowIdx) {
        console.log('[Sheet] Deleting row:', rowIdx);
        sheetData.splice(rowIdx, 1);
        renderSheetTableUI();
        updateCommand();
    }
    
    function addSheetRow() {
        console.log('[Sheet] Adding new row');
        const newRow = {};
        sheetColumns.forEach(col => {
            newRow[col] = '';
        });
        sheetData.push(newRow);
        renderSheetTableUI();
        updateCommand();
    }

    function renderSheetTable() {
        console.log('[Sheet] renderSheetTable called');
        renderSheetTableUI();
    }

    // --- STYLES ---
    const styles = '@import url("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap"); ' +
    '.hoodini-launcher { font-family: "Space Grotesk", sans-serif; background: #fff; color: #1e293b; padding: 24px; border-radius: 12px; width: 100%; box-sizing: border-box; border: 1px solid #e2e8f0; }' +
    '.hoodini-grid { display: grid; grid-template-columns: 3fr 1fr; gap: 24px; }' +
    '@media (max-width: 800px) { .hoodini-grid { grid-template-columns: 1fr; } }' +
    '.main-col { min-width: 0; }' +
    '.sidebar-col { min-width: 0; }' +
    
    '.hoodini-header { display: flex; flex-direction: column; gap: 16px; margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px solid #e2e8f0; }' +
    '.header-top { display: flex; justify-content: space-between; align-items: center; }' +
    '.hoodini-logo { color: #333C45; display: flex; align-items: center; gap: 8px; }' +
    '.hoodini-title { font-size: 20px; font-weight: 700; color: #1e293b; letter-spacing: -0.5px; margin-left: 8px; }' +
    '.hoodini-subtitle { color: #64748b; font-size: 13px; font-weight: 400; }' +
    
    '.mode-switcher { background: #f1f5f9; padding: 4px; border-radius: 8px; display: inline-flex; width: fit-content; }' +
    '.mode-btn { border: none; background: transparent; padding: 6px 16px; border-radius: 9999px; font-family: "Space Grotesk", sans-serif; font-size: 13px; font-weight: 500; color: #0f172a; cursor: pointer; transition: all 0.2s; }' +
    '.mode-btn:hover { color: #0f172a; }' +
    '.mode-btn.active { background: #fff; color: #0f172a; box-shadow: 0 1px 2px rgba(0,0,0,0.05); font-weight: 600; }' +

    '.category-section { margin-bottom: 16px; }' +
    '.category-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; cursor: pointer; user-select: none; }' +
    '.category-toggle { color: #64748b; display: flex; align-items: center; }' +
    '.category-badge { padding: 5px 12px; border-radius: 9999px; font-size: 12px; font-weight: 600; display: inline-flex; align-items: center; gap: 6px; }' +
    '.category-count { color: #64748b; font-size: 11px; }' +
    '.category-content { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; padding: 16px; background: #f8fafc; border-radius: 10px; border: 1px solid #e2e8f0; }' +
    '.category-content.hidden { display: none; }' +
    
    '.param-item { display: flex; flex-direction: column; gap: 4px; }' +
    '.param-label { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 600; color: #1e293b; }' +
    '.param-flag { font-family: monospace; font-size: 10px; color: #64748b; background: #e2e8f0; padding: 2px 6px; border-radius: 4px; }' +
    '.param-desc { font-size: 11px; color: #64748b; line-height: 1.4; }' +
    '.param-input { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px; color: #1e293b; font-size: 13px; width: 100%; box-sizing: border-box; font-family: "Space Grotesk", sans-serif; }' +
    '.param-input:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }' +
    '.param-textarea { background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px; color: #1e293b; font-size: 13px; width: 100%; box-sizing: border-box; font-family: "Space Grotesk", sans-serif; resize: vertical; }' +
    '.param-textarea:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }' +
    '.param-checkbox { display: flex; align-items: center; gap: 8px; cursor: pointer; }' +
    '.checkbox-input { width: 18px; height: 18px; accent-color: #6366f1; cursor: pointer; }' +
    
    '.sidebar-panel { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; height: fit-content; }' +
    '.sidebar-title { font-size: 14px; font-weight: 700; color: #1e293b; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; gap: 8px; }' +
    '.switch-container { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid #f1f5f9; }' +
    '.switch-container:last-child { border-bottom: none; }' +
    '.switch-label { font-size: 13px; font-weight: 500; color: #0f172a; }' +
    '.switch-wrapper { position: relative; display: inline-block; width: 36px; height: 20px; }' +
    '.switch-wrapper input { opacity: 0; width: 0; height: 0; }' +
    '.switch-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #cbd5e1; transition: .4s; border-radius: 34px; }' +
    '.switch-slider:before { position: absolute; content: ""; height: 16px; width: 16px; left: 2px; bottom: 2px; background-color: white; transition: .4s; border-radius: 50%; }' +
    'input:checked + .switch-slider { background-color: #0f172a; }' +
    'input:checked + .switch-slider:before { transform: translateX(16px); }' +
    
    // Multiselect styles
    '.multiselect-container { margin-top: 16px; padding-top: 16px; border-top: 1px solid #e2e8f0; }' +
    '.multiselect-label { font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 4px; }' +
    '.multiselect-desc { font-size: 11px; color: #64748b; margin-bottom: 8px; }' +
    '.multiselect-tags { min-height: 36px; background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px 8px; display: flex; flex-wrap: wrap; gap: 6px; cursor: pointer; }' +
    '.multiselect-tags:hover { border-color: #6366f1; }' +
    '.multiselect-placeholder { color: #94a3b8; font-size: 12px; }' +
    '.multiselect-tag { background: #e0e7ff; color: #4338ca; padding: 3px 8px; border-radius: 9999px; font-size: 11px; font-weight: 500; display: inline-flex; align-items: center; gap: 4px; }' +
    '.tag-remove { cursor: pointer; opacity: 0.7; display: flex; }' +
    '.tag-remove:hover { opacity: 1; }' +
    '.multiselect-dropdown { display: none; position: absolute; background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); max-height: 200px; overflow-y: auto; z-index: 100; margin-top: 4px; width: 100%; }' +
    '.multiselect-dropdown.show { display: block; }' +
    '.multiselect-option { padding: 8px 12px; font-size: 12px; cursor: pointer; }' +
    '.multiselect-option:hover { background: #f1f5f9; }' +
    '.multiselect-container { position: relative; }' +
    
    '.command-section { margin-top: 24px; padding: 16px; background: #1e293b; border-radius: 10px; }' +
    '.command-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }' +
    '.command-title { font-size: 13px; font-weight: 700; color: #fff; display: flex; align-items: center; gap: 6px; }' +
    '.command-output { font-family: monospace; font-size: 12px; color: #4ade80; white-space: pre-wrap; word-break: break-all; margin-bottom: 16px; }' +
    '.btn { padding: 8px 16px; border-radius: 6px; font-size: 13px; font-weight: 600; cursor: pointer; border: none; display: inline-flex; align-items: center; gap: 6px; font-family: "Space Grotesk", sans-serif; transition: 0.2s; }' +
    '.btn-primary { background: #6366f1; color: white; }' +
    '.btn-primary:hover { background: #4f46e5; }' +
    '.btn-secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); }' +
    '.btn-secondary:hover { background: rgba(255,255,255,0.2); }' +
    '.status-badge { padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 600; display: inline-flex; align-items: center; gap: 4px; }' +
    '.status-ready { background: #dcfce7; color: #166534; }' +
    '.status-missing { background: #fef3c7; color: #b45309; }' +
    
    '.sheet-table-container { display: none; margin-bottom: 24px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; }' +
    '.sheet-table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }' +
    '.sheet-table-title { font-size: 14px; font-weight: 700; color: #1e293b; }' +
    '.sheet-table-wrapper { overflow-x: auto; max-height: 400px; overflow-y: auto; }' +
    '.sheet-table { width: 100%; border-collapse: collapse; font-size: 12px; }' +
    '.sheet-table th { background: #1e293b; color: #fff; padding: 8px 6px; text-align: left; font-weight: 600; position: sticky; top: 0; z-index: 10; white-space: nowrap; }' +
    '.sheet-table td { padding: 4px; border-bottom: 1px solid #e2e8f0; }' +
    '.sheet-cell-input { width: 100%; border: 1px solid #e2e8f0; border-radius: 4px; padding: 6px 8px; font-size: 12px; font-family: "Space Grotesk", sans-serif; }' +
    '.sheet-cell-input:focus { outline: none; border-color: #6366f1; }' +
    '.sheet-action-cell { width: 40px; text-align: center; }' +
    '.btn-icon-small { background: transparent; border: none; cursor: pointer; padding: 4px; display: inline-flex; align-items: center; color: #64748b; transition: color 0.2s; }' +
    '.btn-icon-small:hover { color: #ef4444; }' +
    '.btn-add-row:hover { background: #4f46e5; }' +
    '.sheet-simple-table { width: 100%; border-collapse: collapse; font-size: 13px; background: white; margin-top: 8px; }' +
    '.sheet-simple-table thead { background: #2c3e50; color: white; position: sticky; top: 0; z-index: 10; }' +
    '.sheet-header-row th { padding: 8px 10px; text-align: left; font-weight: 600; white-space: nowrap; border-right: 1px solid #1e293b; }' +
    '.sheet-header-row th:last-child { border-right: none; }' +
    '.sheet-data-row { border-bottom: 1px solid #e2e8f0; transition: background 0.15s; }' +
    '.sheet-data-row:hover { background: #f8fafc; }' +
    '.sheet-data-cell { padding: 6px 8px; border-right: 1px solid #e2e8f0; cursor: text; outline: none; }' +
    '.sheet-data-cell:last-of-type { border-right: none; }' +
    '.sheet-data-cell:focus { background: #fff9e6; outline: 2px solid #6366f1; outline-offset: -2px; }' +
    '.sheet-delete-col { width: 40px; text-align: center; padding: 6px; border-right: none; }' +
    '.sheet-delete-btn { background: transparent; border: none; cursor: pointer; color: #94a3b8; display: flex; align-items: center; justify-content: center; transition: color 0.2s; padding: 4px; }' +
    '.sheet-delete-btn:hover { color: #ef4444; }' +
    '.status-indicator { margin-top: 16px; padding: 12px 16px; border-radius: 8px; display: none; align-items: center; gap: 10px; font-size: 13px; font-weight: 500; }' +
    '.status-indicator.show { display: flex; }' +
    '.status-installing { background: #fef3c7; color: #b45309; border: 1px solid #fde68a; }' +
    '.status-running { background: #dbeafe; color: #1e40af; border: 1px solid #bfdbfe; }' +
    '.status-finished { background: #dcfce7; color: #166534; border: 1px solid #bbf7d0; }' +
    '.status-error { background: #fee2e2; color: #991b1b; border: 1px solid #fecaca; }' +
    '.spinner-icon { animation: spin 1s linear infinite; }' +
    '.log-section { margin-top: 16px; background: #0f172a; color: #e2e8f0; border-radius: 8px; border: 1px solid #1e293b; padding: 12px; }' +
    '.log-header { display: flex; align-items: center; justify-content: space-between; gap: 8px; }' +
    '.log-title { font-size: 13px; font-weight: 700; display: flex; align-items: center; gap: 8px; }' +
    '.log-content { margin-top: 10px; max-height: 260px; overflow: auto; background: #0b1220; padding: 12px; border-radius: 6px; font-family: monospace; font-size: 12px; white-space: pre-wrap; color: #e2e8f0; border: 1px solid #1e293b; }' +
    '.btn-sm { padding: 6px 10px; font-size: 12px; }' +
    '@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }';

    el.innerHTML = '<style>' + styles + '</style>';

    // --- RENDER ---
    const launcher = document.createElement('div');
    launcher.className = 'hoodini-launcher';

    // 1. Header with Mode Switcher
    const header = document.createElement('div');
    header.className = 'hoodini-header';
    
    const topRow = document.createElement('div');
    topRow.className = 'header-top';
    topRow.innerHTML = 
        '<div style="display: flex; flex-direction: column; gap: 8px;">' +
        '<div style="display: flex; align-items: center;">' +
        '<div class="hoodini-logo">' + icons.dna + icons.colab + '</div>' +
        '<span class="hoodini-title">Hoodini Colab Launcher</span>' +
        '</div>' +
        '<div class="hoodini-subtitle">Magic gene-neighborhood analyses in Google Colab</div>' +
        '</div>' +
        '<span class="status-badge status-missing">' + icons.alert + ' Input required</span>';
    
    const modeRow = document.createElement('div');
    modeRow.className = 'mode-switcher';
    ['Single Input', 'Input List', 'Input Sheet'].forEach((m, idx) => {
        const key = ['single', 'list', 'sheet'][idx];
        const btn = document.createElement('button');
        btn.className = 'mode-btn' + (key === currentMode ? ' active' : '');
        btn.textContent = m;
        btn.onclick = () => {
            currentMode = key;
            el.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateVisibility();
        };
        modeRow.appendChild(btn);
    });
    header.appendChild(topRow);
    header.appendChild(modeRow);
    launcher.appendChild(header);

    // Sheet Table (for Input Sheet mode)
    const sheetTableContainer = document.createElement('div');
    sheetTableContainer.className = 'sheet-table-container';
    
    const sheetHeader = document.createElement('div');
    sheetHeader.className = 'sheet-table-header';
    sheetHeader.innerHTML = '<div class="sheet-table-title">Input Sheet Data</div>';
    
    const btnAddRow = document.createElement('button');
    btnAddRow.className = 'btn btn-primary';
    btnAddRow.innerHTML = icons.plus + ' Add Row';
    btnAddRow.onclick = () => addSheetRow();
    sheetHeader.appendChild(btnAddRow);
    sheetTableContainer.appendChild(sheetHeader);
    
    const tableWrapper = document.createElement('div');
    tableWrapper.className = 'sheet-table-wrapper';
    const tableHost = document.createElement('div');
    tableHost.id = 'sheet-table';
    tableWrapper.appendChild(tableHost);
    sheetTableContainer.appendChild(tableWrapper);
    
    launcher.appendChild(sheetTableContainer);

    // 2. Grid Content
    const grid = document.createElement('div');
    grid.className = 'hoodini-grid';

    // Left Column: Main Params
    const mainCol = document.createElement('div');
    mainCol.className = 'main-col';
    
    const collapsedState = {};

    Object.entries(params).forEach(([category, paramList]) => {
        if (category === 'Annotations' || category === 'Links') return; // Goes to sidebar
        
        const section = document.createElement('div');
        section.className = 'category-section';
        section.setAttribute('data-category', category);
        
        const style = categoryStyles[category] || { bg: '#f1f5f9', text: '#475569' };
        collapsedState[category] = (category !== 'Input/Output');
        
        const catHeader = document.createElement('div');
        catHeader.className = 'category-header';
        catHeader.innerHTML = 
            '<span class="category-toggle">' + (collapsedState[category] ? icons.chevronRight : icons.chevronDown) + '</span>' +
            '<span class="category-badge" style="background: ' + style.bg + '; color: ' + style.text + '">' + category + '</span>' +
            '<span class="category-count">' + paramList.length + ' options</span>';
            
        const content = document.createElement('div');
        content.className = 'category-content' + (collapsedState[category] ? ' hidden' : '');
        
        paramList.forEach(param => {
            content.appendChild(createInput(param));
        });
        
        catHeader.onclick = () => {
            collapsedState[category] = !collapsedState[category];
            content.classList.toggle('hidden', collapsedState[category]);
            const toggle = catHeader.querySelector('.category-toggle');
            toggle.innerHTML = collapsedState[category] ? icons.chevronRight : icons.chevronDown;
        };
        
        section.appendChild(catHeader);
        section.appendChild(content);
        mainCol.appendChild(section);
    });
    grid.appendChild(mainCol);

    // Right Column: Annotations + Links Sidebar
    const sidebarCol = document.createElement('div');
    sidebarCol.className = 'sidebar-col';
    
    // Annotations Section
    const annotStyle = categoryStyles['Annotations'] || { bg: '#f1f5f9', text: '#475569' };
    const annotSection = document.createElement('div');
    annotSection.className = 'category-section';
    annotSection.setAttribute('data-category', 'Annotations');
    const annotHeader = document.createElement('div');
    annotHeader.className = 'category-header';
    annotHeader.innerHTML = '<span class="category-toggle">' + icons.chevronDown + '</span>' + '<span class="category-badge" style="background: ' + annotStyle.bg + '; color: ' + annotStyle.text + '">Annotations</span>' + '<span class="category-count">' + (params['Annotations'] ? params['Annotations'].length : 0) + ' options</span>';
    const annotContent = document.createElement('div');
    annotContent.className = 'sidebar-panel';
    
    if (params['Annotations']) {
        params['Annotations'].forEach(param => {
            if (param.type === 'bool' || param.type === 'switch') {
                annotContent.appendChild(createSwitch(param));
            } else if (param.type === 'multiselect') {
                annotContent.appendChild(createMultiSelect(param));
            } else {
                const wrap = document.createElement('div');
                wrap.style.marginTop = '12px';
                wrap.appendChild(createInput(param));
                annotContent.appendChild(wrap);
            }
        });
    }
    
    annotHeader.onclick = () => {
        annotContent.classList.toggle('hidden');
        const toggle = annotHeader.querySelector('.category-toggle');
        toggle.innerHTML = annotContent.classList.contains('hidden') ? icons.chevronRight : icons.chevronDown;
    };
    
    annotSection.appendChild(annotHeader);
    annotSection.appendChild(annotContent);
    sidebarCol.appendChild(annotSection);
    
    // Links Section
    const linksStyle = categoryStyles['Links'] || { bg: '#f1f5f9', text: '#475569' };
    const linksSection = document.createElement('div');
    linksSection.className = 'category-section';
    linksSection.setAttribute('data-category', 'Links');
    const linksHeader = document.createElement('div');
    linksHeader.className = 'category-header';
    linksHeader.innerHTML = '<span class="category-toggle">' + icons.chevronDown + '</span>' + '<span class="category-badge" style="background: ' + linksStyle.bg + '; color: ' + linksStyle.text + '">Links</span>' + '<span class="category-count">' + (params['Links'] ? params['Links'].length : 0) + ' options</span>';
    const linksContent = document.createElement('div');
    linksContent.className = 'sidebar-panel';
    
    if (params['Links']) {
        params['Links'].forEach(param => {
            if (param.type === 'bool' || param.type === 'switch') {
                linksContent.appendChild(createSwitch(param));
            } else {
                const wrap = document.createElement('div');
                wrap.style.marginTop = '12px';
                wrap.appendChild(createInput(param));
                linksContent.appendChild(wrap);
            }
        });
    }
    
    linksHeader.onclick = () => {
        linksContent.classList.toggle('hidden');
        const toggle = linksHeader.querySelector('.category-toggle');
        toggle.innerHTML = linksContent.classList.contains('hidden') ? icons.chevronRight : icons.chevronDown;
    };
    
    linksSection.appendChild(linksHeader);
    linksSection.appendChild(linksContent);
    sidebarCol.appendChild(linksSection);
    
    grid.appendChild(sidebarCol);
    launcher.appendChild(grid);

    // 3. Command Footer
    const cmdSection = document.createElement('div');
    cmdSection.className = 'command-section';
    cmdSection.innerHTML = 
        '<div class="command-header">' +
            '<div class="command-title">' + icons.terminal + ' Generated Command</div>' +
            '<div class="btn-group" style="display:flex; gap:8px">' +
    
    // Status Indicator
                '<button id="copy-btn" class="btn btn-secondary">' + icons.copy + ' Copy</button>' +
                '<button id="reset-btn" class="btn btn-secondary">' + icons.refresh + ' Reset</button>' +
            '</div>' +
        '</div>' +
        '<pre class="command-output">hoodini run</pre>' +
        '<button id="run-btn" class="btn btn-primary" style="width:100%">' + icons.play + ' Run Hoodini Analysis</button>';
    launcher.appendChild(cmdSection);
    
    // Status Indicator
    const statusIndicator = document.createElement('div');
    statusIndicator.className = 'status-indicator';
    statusIndicator.id = 'status-indicator';
    launcher.appendChild(statusIndicator);

    // Logs panel (collapsible)
    const logsSection = document.createElement('div');
    logsSection.className = 'log-section';
    logsSection.innerHTML =
        '<div class="log-header">' +
            '<div class="log-title">' + icons.terminal + ' Logs</div>' +
            '<button id="toggle-logs" class="btn btn-secondary btn-sm">' + icons.chevronRight + ' Show logs</button>' +
        '</div>' +
        '<pre id="log-content" class="log-content" style="display:none"></pre>';
    launcher.appendChild(logsSection);
    
    // HTML Visualization Container
    const htmlVisualizationContainer = document.createElement('div');
    htmlVisualizationContainer.id = 'html-visualization-container';
    htmlVisualizationContainer.style.display = 'none';
    htmlVisualizationContainer.style.marginTop = '20px';
    htmlVisualizationContainer.innerHTML = 
        '<div style="background:#f8f9fa; border:1px solid #e0e0e0; border-radius:8px; padding:16px">' +
        '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px">' +
        '<h3 style="margin:0; font-size:16px; font-weight:600">📊 Interactive Visualization</h3>' +
        '<button id="download-html-btn" class="btn btn-secondary" style="padding:6px 12px">' + icons.copy + ' Download HTML</button>' +
        '</div>' +
        '<iframe id="html-viewer" style="width:100%; height:800px; border:1px solid #ddd; border-radius:4px"></iframe>' +
        '</div>';
    launcher.appendChild(htmlVisualizationContainer);
    
    el.appendChild(launcher);
    
    // Listen for status changes from Python
    model.on('change:status_state', () => {
        const state = model.get('status_state');
        const message = model.get('status_message');
        const indicator = el.querySelector('#status-indicator');
        
        if (state === 'idle') {
            indicator.classList.remove('show');
            indicator.className = 'status-indicator';
        } else {
            indicator.classList.add('show');
            indicator.className = 'status-indicator show';
            
            if (state === 'installing' || state === 'installing_launcher' || state === 'installing_hoodini') {
                indicator.classList.add('status-installing');
                indicator.innerHTML = icons.spinner + ' <strong>Installing:</strong> ' + message;
            } else if (state === 'downloading_databases') {
                indicator.classList.add('status-installing');
                indicator.innerHTML = icons.spinner + ' <strong>Downloading:</strong> ' + message;
            } else if (state === 'running') {
                indicator.classList.add('status-running');
                indicator.innerHTML = icons.spinner + ' <strong>Running:</strong> ' + message;
            } else if (state === 'finished') {
                indicator.classList.add('status-finished');
                indicator.innerHTML = icons.check + ' <strong>Finished!</strong> ' + message;
            } else if (state === 'error') {
                indicator.classList.add('status-error');
                indicator.innerHTML = icons.alert + ' <strong>Error:</strong> ' + message;
            }
        }
    });

    // Listen for logs and handle collapsible panel
    const logContentEl = el.querySelector('#log-content');
    const toggleLogsBtn = el.querySelector('#toggle-logs');
    let logsOpen = false;

    function updateLogsVisibility() {
        if (!logContentEl || !toggleLogsBtn) return;
        logContentEl.style.display = logsOpen ? 'block' : 'none';
        toggleLogsBtn.innerHTML = (logsOpen ? icons.chevronDown + ' Hide logs' : icons.chevronRight + ' Show logs');
        if (logsOpen) {
            logContentEl.scrollTop = logContentEl.scrollHeight;
        }
    }

    if (toggleLogsBtn) {
        toggleLogsBtn.onclick = () => {
            logsOpen = !logsOpen;
            updateLogsVisibility();
        };
    }

    model.on('change:logs', () => {
        if (!logContentEl) return;
        const logs = model.get('logs') || '';
        logContentEl.textContent = logs;
        updateLogsVisibility();
    });

    // Listen for HTML output
    model.on('change:html_output', () => {
        const htmlContent = model.get('html_output');
        if (htmlContent) {
            const container = el.querySelector('#html-visualization-container');
            const iframeViewer = el.querySelector('#html-viewer');
            
            // Display the HTML in iframe using blob URL
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const blobUrl = URL.createObjectURL(blob);
            iframeViewer.src = blobUrl;
            
            container.style.display = 'block';
        }
    });

    // Handlers
    el.querySelector('#copy-btn').onclick = function() {
        const cmd = buildCommand();
        navigator.clipboard.writeText(cmd);
        const btn = el.querySelector('#copy-btn');
        btn.innerHTML = icons.check + ' Copied';
        setTimeout(() => { btn.innerHTML = icons.copy + ' Copy'; }, 2000);
    };

    el.querySelector('#run-btn').onclick = () => {
        model.set('run_requested', true);
        model.save_changes();
    };

    el.querySelector('#download-html-btn').onclick = () => {
        const htmlContent = model.get('html_output');
        if (htmlContent) {
            const blob = new Blob([htmlContent], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'hoodini-visualization.html';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        }
    };

    el.querySelector('#reset-btn').onclick = () => {
        // Clear all state (leave empty like initial load)
        Object.keys(state).forEach(k => delete state[k]);
        Object.keys(multiSelectState).forEach(k => multiSelectState[k] = []);
        
        // Reset all text/number inputs - show defaults but don't set in state
        el.querySelectorAll('input[type="text"], input[type="number"], textarea').forEach(input => {
            const paramName = input.closest('.param-item')?.querySelector('.param-flag')?.textContent?.replace('--', '');
            if (paramName) {
                const param = Object.values(params).flat().find(p => p.name === paramName);
                // Display default value in input, but don't add to state
                if (param && param.def !== undefined) {
                    input.value = param.def;
                } else {
                    input.value = '';
                }
            } else {
                input.value = '';
            }
        });
        
        // Reset all selects - show defaults but don't set in state
        el.querySelectorAll('select').forEach(select => {
            const paramName = select.closest('.param-item')?.querySelector('.param-flag')?.textContent?.replace('--', '');
            if (paramName) {
                const param = Object.values(params).flat().find(p => p.name === paramName);
                // Display default value in select, but don't add to state
                if (param && param.def !== undefined) {
                    select.value = param.def;
                } else {
                    select.value = '';
                }
            } else {
                select.value = '';
            }
        });
        
        // Reset all switches/checkboxes to their defaults
        el.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
            const switchContainer = checkbox.closest('.switch-container');
            if (switchContainer) {
                // This is a switch - check for default value
                const label = switchContainer.querySelector('.switch-label')?.textContent;
                if (label) {
                    const param = Object.values(params).flat().find(p => p.label === label);
                    const defaultVal = param && param.def !== undefined ? param.def : false;
                    checkbox.checked = defaultVal;
                    // Only add to state if default is true
                    if (defaultVal) {
                        state[param.name] = defaultVal;
                    }
                }
            } else {
                // Regular checkbox
                checkbox.checked = false;
            }
        });
        
        // Reset multiselect
        el.querySelectorAll('.multiselect-tags').forEach(container => {
            container.innerHTML = '<span class="multiselect-placeholder">Click to select databases...</span>';
        });

        updateVisibility();
        updateCommand();
    };
    
    // Initialize logs panel state
    if (typeof updateLogsVisibility === 'function') {
        updateLogsVisibility();
    }

    // Heartbeat to keep Colab session active without blocking kernel
    let heartbeatCounter = 0;
    setInterval(() => {
        heartbeatCounter += 1;
        model.set('heartbeat', heartbeatCounter);
        model.save_changes();
    }, 30000); // 30s ping

    // Initialize with one empty row for sheet mode
    addSheetRow();
    updateVisibility();
    model.set('command', buildCommand());
    model.save_changes();
}
export default { render };