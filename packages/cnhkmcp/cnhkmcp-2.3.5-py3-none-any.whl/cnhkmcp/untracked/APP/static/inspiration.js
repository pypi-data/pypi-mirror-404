/**
 * Inspiration Master - Frontend Logic
 */

// Global state for inspiration feature
let inspirationState = {
    isLoggedIn: false,
    llmConfig: {
        baseUrl: "https://api.moonshot.cn/v1",
        model: "kimi-k2.5",
        apiKey: ""
    },
    options: null,
    selectedDataset: null,
    selectedDatasetCategory: null,
    pipelineTaskId: null,
    pipelineEventSource: null,
    enhanceTaskId: null,
    enhanceDataType: 'MATRIX'
};

document.addEventListener('DOMContentLoaded', function() {
    const inspirationBtn = document.getElementById('inspirationBtn');
    if (inspirationBtn) {
        inspirationBtn.addEventListener('click', openInspirationModal);
    }

    // Initialize event listeners for the modal
    document.getElementById('inspire-region').addEventListener('change', updateUniversesAndDelays);
    document.getElementById('inspire-search-dataset').addEventListener('click', searchDatasets);
    document.getElementById('inspire-generate').addEventListener('click', generateAlphaTemplates);
    document.getElementById('inspire-download').addEventListener('click', downloadInspirationResult);
    document.getElementById('inspire-new-task').addEventListener('click', resetInspirationTask);
    document.getElementById('inspire-close').addEventListener('click', closeInspirationModal);
    const directBtn = document.getElementById('inspire-direct');
    if (directBtn) {
        directBtn.addEventListener('click', runDirectAlphaPipeline);
    }
    const directDlBtn = document.getElementById('inspire-direct-download');
    if (directDlBtn) {
        directDlBtn.addEventListener('click', downloadPipelineZip);
    }
    
    const testBtn = document.getElementById('inspire-test-llm');
    if (testBtn) {
        testBtn.addEventListener('click', testLLMConnection);
    }
    const enhanceBtn = document.getElementById('inspire-enhance');
    if (enhanceBtn) {
        enhanceBtn.addEventListener('click', () => {
            openEnhanceDataTypeModal();
        });
    }
    const enhanceInput = document.getElementById('inspire-idea-file');
    if (enhanceInput) {
        enhanceInput.addEventListener('change', handleEnhanceFile);
    }
    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    if (enhanceDlBtn) {
        enhanceDlBtn.addEventListener('click', downloadEnhanceZip);
    }

    // Enhance data type modal wiring
    const dtypeClose = document.getElementById('enhance-datatype-close');
    if (dtypeClose) dtypeClose.addEventListener('click', closeEnhanceDataTypeModal);
    const dtypeCancel = document.getElementById('enhance-datatype-cancel');
    if (dtypeCancel) dtypeCancel.addEventListener('click', closeEnhanceDataTypeModal);
    const dtypeConfirm = document.getElementById('enhance-datatype-confirm');
    if (dtypeConfirm) dtypeConfirm.addEventListener('click', confirmEnhanceDataType);
    
    // Initially disable generate button until tested
    const genBtn = document.getElementById('inspire-generate');
    if (genBtn) {
        genBtn.disabled = true;
        genBtn.title = "Please test LLM connection first";
    }
    
    // Initially disable new task button
    const newTaskBtn = document.getElementById('inspire-new-task');
    if (newTaskBtn) {
        newTaskBtn.disabled = true;
        newTaskBtn.style.opacity = '0.5';
        newTaskBtn.style.cursor = 'not-allowed';
    }

    // Check login status periodically or on load to update button state
    checkLoginAndUpdateButton();
});

function getHeaders() {
    const headers = {'Content-Type': 'application/json'};
    const sessionId = localStorage.getItem('brain_session_id');
    if (sessionId) {
        headers['Session-ID'] = sessionId;
    }
    return headers;
}

function checkLoginAndUpdateButton() {
    fetch('/api/check_login', { headers: getHeaders() })
        .then(response => response.json())
        .then(data => {
            const btn = document.getElementById('inspirationBtn');
            if (data.logged_in) {
                inspirationState.isLoggedIn = true;
                if (btn) {
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                    btn.disabled = false;
                }
            } else {
                inspirationState.isLoggedIn = false;
                if (btn) {
                    btn.style.opacity = '0.5';
                    btn.style.cursor = 'not-allowed';
                    btn.disabled = true;
                }
            }
        })
        .catch(err => {
            console.error("Error checking login status:", err);
            const btn = document.getElementById('inspirationBtn');
            if (btn) {
                btn.disabled = true;
                btn.style.opacity = '0.5';
                btn.style.cursor = 'not-allowed';
            }
        });
}

// Expose this function globally so other scripts (like brain.js) can call it after login
window.updateInspirationButtonState = checkLoginAndUpdateButton;

function openInspirationModal() {
    if (!inspirationState.isLoggedIn) {
        // Double check
        fetch('/api/check_login', { headers: getHeaders() })
            .then(response => response.json())
            .then(data => {
                if (data.logged_in) {
                    inspirationState.isLoggedIn = true;
                    document.getElementById('inspirationModal').style.display = 'block';
                    loadInspirationOptions();
                } else {
                    // Trigger Brain Login Modal
                    if (typeof openBrainLoginModal === 'function') {
                        openBrainLoginModal();
                    } else {
                        alert("请先登录 BRAIN。");
                    }
                }
            });
        return;
    }
    document.getElementById('inspirationModal').style.display = 'block';
    loadInspirationOptions();
}
function closeInspirationModal() {
    document.getElementById('inspirationModal').style.display = 'none';
}

function loadInspirationOptions() {
    if (inspirationState.options) return; // Already loaded

    fetch('/api/inspiration/options', { headers: getHeaders() })
        .then(res => res.json())
        .then(data => {
            inspirationState.options = data;
            populateRegionDropdown(data);
        })
        .catch(err => console.error("Failed to load options:", err));
}

function populateRegionDropdown(data) {
    const regionSelect = document.getElementById('inspire-region');
    regionSelect.innerHTML = '<option value="">Select Region</option>';
    
    // Assuming data structure matches what we get from ace_lib
    // Structure: { "EQUITY": { "USA": { ... }, "CHN": { ... } } }
    // We'll focus on EQUITY for now or iterate all
    
    let regions = new Set();
    if (data.EQUITY) {
        Object.keys(data.EQUITY).forEach(r => regions.add(r));
    }
    
    regions.forEach(r => {
        const option = document.createElement('option');
        option.value = r;
        option.textContent = r;
        regionSelect.appendChild(option);
    });
}

function updateUniversesAndDelays() {
    const region = document.getElementById('inspire-region').value;
    const universeSelect = document.getElementById('inspire-universe');
    const delaySelect = document.getElementById('inspire-delay');
    
    universeSelect.innerHTML = '<option value="">Select Universe</option>';
    delaySelect.innerHTML = '<option value="">Select Delay</option>';
    
    if (!region || !inspirationState.options || !inspirationState.options.EQUITY || !inspirationState.options.EQUITY[region]) return;
    
    const data = inspirationState.options.EQUITY[region];
    
    data.universes.forEach(u => {
        const option = document.createElement('option');
        option.value = u;
        option.textContent = u;
        universeSelect.appendChild(option);
    });
    
    data.delays.forEach(d => {
        const option = document.createElement('option');
        option.value = d;
        option.textContent = d;
        delaySelect.appendChild(option);
    });
}

function searchDatasets() {
    const region = document.getElementById('inspire-region').value;
    const delay = document.getElementById('inspire-delay').value;
    const universe = document.getElementById('inspire-universe').value;
    const search = document.getElementById('inspire-dataset-search').value;
    
    if (!region || !delay || !universe) {
        alert("请先选择区域、延迟和股票池。");
        return;
    }
    
    const resultsDiv = document.getElementById('inspire-dataset-results');
    resultsDiv.innerHTML = '正在加载数据集...';
    
    fetch('/api/inspiration/datasets', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ region, delay, universe, search })
    })
    .then(res => res.json())
    .then(data => {
        displayDatasetResults(data);
    })
    .catch(err => {
        resultsDiv.innerHTML = '加载数据集出错: ' + err;
    });
}

function displayDatasetResults(datasets) {
    const resultsDiv = document.getElementById('inspire-dataset-results');
    resultsDiv.innerHTML = '';
    
    if (datasets.length === 0) {
        resultsDiv.innerHTML = '未找到数据集。';
        return;
    }
    
    const table = document.createElement('table');
    table.className = 'dataset-table'; 
    table.style.width = '100%'; // Ensure full width
    table.style.borderCollapse = 'collapse';
    
    table.innerHTML = `
        <thead>
            <tr style="text-align: left; background: #f1f1f1;">
                <th style="padding: 8px; border-bottom: 1px solid #ddd;">ID</th>
                <th style="padding: 8px; border-bottom: 1px solid #ddd;">Name</th>
                <th style="padding: 8px; border-bottom: 1px solid #ddd;">Category</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    
    const tbody = table.querySelector('tbody');
    
    datasets.forEach(ds => {
        const tr = document.createElement('tr');
        tr.dataset.id = ds.id;
        tr.style.cursor = 'pointer';
        tr.style.transition = 'background-color 0.2s';
        
        // Fix [object Object] issue for category
        let category = ds.category;
        if (typeof category === 'object' && category !== null) {
            // Try to find a meaningful string representation
            category = category.name || category.id || JSON.stringify(category);
        }
        
        tr.innerHTML = `
            <td style="padding: 8px; border-bottom: 1px solid #eee; color: #007bff; font-weight: bold;">${ds.id}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">${ds.name}</td>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">${category}</td>
        `;
        
        tr.addEventListener('click', function() {
            selectDataset(ds.id, category);
        });
        
        tr.addEventListener('mouseenter', function() {
            if (inspirationState.selectedDataset !== ds.id) {
                this.style.backgroundColor = '#f8f9fa';
            }
        });
        
        tr.addEventListener('mouseleave', function() {
            if (inspirationState.selectedDataset !== ds.id) {
                this.style.backgroundColor = '';
            }
        });

        tbody.appendChild(tr);
    });
    
    resultsDiv.appendChild(table);
}

function selectDataset(id, category) {
    inspirationState.selectedDataset = id;
    inspirationState.selectedDatasetCategory = category || null;
    const display = document.getElementById('inspire-selected-dataset');
    if (display) {
        display.textContent = "已选数据集: " + id;
        display.style.display = 'block';
    }
    
    // Highlight the selected row
    document.querySelectorAll('.dataset-table tr').forEach(tr => tr.style.backgroundColor = '');
    const row = document.querySelector(`.dataset-table tr[data-id="${id}"]`);
    if (row) {
        row.style.backgroundColor = '#e7f1ff';
    }
}

// Removed toggleAccordion as we are moving to a horizontal layout

function generateAlphaTemplates() {
    if (!inspirationState.selectedDataset) {
        alert("请先选择一个数据集。");
        return;
    }
    
    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;
    
    if (!apiKey) {
        alert("请输入 LLM API Key。");
        return;
    }
    
    const region = document.getElementById('inspire-region').value;
    const delay = document.getElementById('inspire-delay').value;
    const universe = document.getElementById('inspire-universe').value;
    const dataType = (document.getElementById('inspire-data-type') || {}).value || 'MATRIX';
    
    const outputDiv = document.getElementById('inspire-output');
    outputDiv.innerHTML = '正在生成模板... 这可能需要几分钟...';
    
    fetch('/api/inspiration/generate', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            apiKey, baseUrl, model,
            region, delay, universe,
            datasetId: inspirationState.selectedDataset,
            dataType
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            outputDiv.innerHTML = '错误: ' + data.error;
        } else {
            // Render Markdown
            // Assuming marked.js or similar is available, or just text for now
            // If you have a markdown renderer, use it.
            // For now, simple text or basic HTML replacement
            outputDiv.innerHTML = formatMarkdown(data.result);
            inspirationState.lastResult = data.result;
            const dlBtn = document.getElementById('inspire-download');
            if (dlBtn) dlBtn.style.display = 'inline-block';
            
            const newTaskBtn = document.getElementById('inspire-new-task');
            if (newTaskBtn) {
                newTaskBtn.disabled = false;
                newTaskBtn.style.opacity = '1';
                newTaskBtn.style.cursor = 'pointer';
            }
        }
    })
    .catch(err => {
        outputDiv.innerHTML = '生成模板出错: ' + err;
    });
}

function runDirectAlphaPipeline() {
    if (!inspirationState.selectedDataset) {
        alert("请先选择一个数据集。");
        return;
    }

    const region = document.getElementById('inspire-region').value;
    const delay = document.getElementById('inspire-delay').value;
    const universe = document.getElementById('inspire-universe').value;
    const dataType = (document.getElementById('inspire-data-type') || {}).value || 'MATRIX';
    const dataCategory = inspirationState.selectedDatasetCategory;

    if (!region || !delay || !universe) {
        alert("请先选择区域、延迟和股票池。");
        return;
    }

    if (!dataCategory) {
        alert("当前数据集没有可用的分类信息，无法运行。请重新搜索并选择数据集。");
        return;
    }

    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;

    if (!apiKey) {
        alert('请先填写 LLM API Key。');
        return;
    }

    const outputDiv = document.getElementById('inspire-output');
    outputDiv.innerHTML = '<pre id="inspire-stream" style="white-space: pre-wrap; margin: 0;"></pre>';

    const directBtn = document.getElementById('inspire-direct');
    if (directBtn) {
        directBtn.disabled = true;
        directBtn.textContent = '正在运行...';
    }

    const dlBtn = document.getElementById('inspire-direct-download');
    if (dlBtn) dlBtn.style.display = 'none';

    if (inspirationState.pipelineEventSource) {
        inspirationState.pipelineEventSource.close();
        inspirationState.pipelineEventSource = null;
    }

    fetch('/api/inspiration/run-pipeline', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
            datasetId: inspirationState.selectedDataset,
            dataCategory,
            region,
            delay,
            universe,
            dataType,
            apiKey,
            baseUrl,
            model
        })
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            outputDiv.innerHTML = '启动失败: ' + (data.error || '未知错误');
            if (directBtn) {
                directBtn.disabled = false;
                directBtn.textContent = '直接来点 Alpha';
            }
            return;
        }

        inspirationState.pipelineTaskId = data.taskId;
        startPipelineStream(data.taskId);
    })
    .catch(err => {
        outputDiv.innerHTML = '启动出错: ' + err;
        if (directBtn) {
            directBtn.disabled = false;
            directBtn.textContent = '直接来点 Alpha';
        }
    });
}

function startPipelineStream(taskId) {
    const streamEl = document.getElementById('inspire-stream');
    const outputDiv = document.getElementById('inspire-output');
    if (!streamEl) {
        outputDiv.innerHTML = '<pre id="inspire-stream" style="white-space: pre-wrap; margin: 0;"></pre>';
    }
    const target = document.getElementById('inspire-stream');

    const source = new EventSource(`/api/inspiration/stream-pipeline/${taskId}`);
    inspirationState.pipelineEventSource = source;

    source.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload && payload.line !== undefined) {
                target.textContent += payload.line + '\n';
                outputDiv.scrollTop = outputDiv.scrollHeight;
            }
        } catch {
            target.textContent += event.data + '\n';
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }
    };

    source.addEventListener('done', (event) => {
        let info = null;
        try {
            info = JSON.parse(event.data);
        } catch {
            info = { success: false };
        }
        const directBtn = document.getElementById('inspire-direct');
        if (directBtn) {
            directBtn.disabled = false;
            directBtn.textContent = '直接来点 Alpha';
        }

        if (info && info.success) {
            target.textContent += '\n✅ 运行完成，可下载结果 ZIP。\n';
            const dlBtn = document.getElementById('inspire-direct-download');
            if (dlBtn) dlBtn.style.display = 'inline-block';
        } else {
            target.textContent += '\n❌ 运行失败，请检查日志。\n';
        }

        source.close();
        inspirationState.pipelineEventSource = null;
    });

    source.addEventListener('error', () => {
        const directBtn = document.getElementById('inspire-direct');
        if (directBtn) {
            directBtn.disabled = false;
            directBtn.textContent = '直接来点 Alpha';
        }
        target.textContent += '\n⚠️ 日志流中断。\n';
        source.close();
        inspirationState.pipelineEventSource = null;
    });
}

function downloadPipelineZip() {
    if (!inspirationState.pipelineTaskId) return;
    window.location.href = `/api/inspiration/download-pipeline/${inspirationState.pipelineTaskId}`;
}

function formatMarkdown(text) {
    if (typeof marked !== 'undefined') {
        // Split text by code blocks (triple backticks or single backticks)
        // We want to escape < and > in normal text, but NOT in code blocks
        const parts = text.split(/(```[\s\S]*?```|`[^`]*`)/g);
        
        const escapedParts = parts.map(part => {
            // If it starts with backtick, it's a code block -> return as is
            if (part.startsWith('`')) {
                return part;
            }
            // Otherwise, escape < and >
            return part.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        });
        
        return marked.parse(escapedParts.join(''));
    }
    
    // Fallback simple formatter
    // Here we DO need to escape because we are building HTML manually
    const escapedText = text.replace(/</g, '&lt;').replace(/>/g, '&gt;');
    let html = escapedText
        .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
        .replace(/\n/g, '<br>');
    return html;
}

function testLLMConnection() {
    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;
    const testBtn = document.getElementById('inspire-test-llm');
    const generateBtn = document.getElementById('inspire-generate');
    const enhanceBtn = document.getElementById('inspire-enhance');
    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    
    if (!apiKey) {
        alert("请先输入 API Key。");
        return;
    }
    
    testBtn.textContent = "测试中...";
    testBtn.disabled = true;
    
    fetch('/api/inspiration/test_llm', {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ apiKey, baseUrl, model })
    })
    .then(res => res.json())
    .then(data => {
        testBtn.disabled = false;
        if (data.success) {
            testBtn.textContent = "成功";
            testBtn.className = "btn btn-success";
            generateBtn.disabled = false;
            if (enhanceBtn) enhanceBtn.disabled = false;
            if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
            setTimeout(() => { testBtn.textContent = "测试连接"; testBtn.className = "btn btn-secondary"; }, 3000);
        } else {
            testBtn.textContent = "失败";
            testBtn.className = "btn btn-danger";
            alert("连接失败: " + data.error);
            generateBtn.disabled = true;
            if (enhanceBtn) enhanceBtn.disabled = true;
            if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
            setTimeout(() => { testBtn.textContent = "测试连接"; testBtn.className = "btn btn-secondary"; }, 3000);
        }
    })
    .catch(err => {
        testBtn.disabled = false;
        testBtn.textContent = "错误";
        alert("错误: " + err);
        if (enhanceBtn) enhanceBtn.disabled = true;
        if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
    });
}

function handleEnhanceFile(event) {
    const files = event.target.files ? Array.from(event.target.files) : [];
    if (files.length === 0) return;

    const apiKey = document.getElementById('inspire-llm-key').value;
    const baseUrl = document.getElementById('inspire-llm-url').value;
    const model = document.getElementById('inspire-llm-model').value;
    if (!apiKey) {
        alert("请输入 LLM API Key。");
        return;
    }

    const outputDiv = document.getElementById('inspire-output');
    outputDiv.innerHTML = '<pre id="inspire-enhance-stream" style="white-space: pre-wrap; margin: 0;"></pre>';

    const enhanceBtn = document.getElementById('inspire-enhance');
    if (enhanceBtn) {
        enhanceBtn.disabled = true;
        enhanceBtn.textContent = '处理中...';
    }
    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';

    const formData = new FormData();
    files.forEach(file => formData.append('ideaFiles', file));
    formData.append('apiKey', apiKey);
    formData.append('baseUrl', baseUrl);
    formData.append('model', model);
    formData.append('dataType', inspirationState.enhanceDataType || 'MATRIX');

    fetch('/api/inspiration/enhance-template', {
        method: 'POST',
        headers: { 'Session-ID': localStorage.getItem('brain_session_id') || '' },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (!data.success) {
            outputDiv.innerHTML = '启动失败: ' + (data.error || '未知错误');
            if (enhanceBtn) {
                enhanceBtn.disabled = false;
                enhanceBtn.textContent = '增强历史生成模板';
            }
            return;
        }
        inspirationState.enhanceTaskId = data.taskId;
        startEnhanceStream(data.taskId, files.length);
    })
    .catch(err => {
        outputDiv.innerHTML = '启动出错: ' + err;
        if (enhanceBtn) {
            enhanceBtn.disabled = false;
            enhanceBtn.textContent = '增强历史生成模板';
        }
    })
    .finally(() => {
        event.target.value = '';
    });
}

function openEnhanceDataTypeModal() {
    const modal = document.getElementById('enhanceDataTypeModal');
    if (!modal) {
        // Fallback: if modal missing, proceed with default.
        const input = document.getElementById('inspire-idea-file');
        if (input) input.click();
        return;
    }

    // Default to MATRIX each time unless user already picked.
    const sel = document.getElementById('inspire-enhance-data-type');
    if (sel) sel.value = inspirationState.enhanceDataType || 'MATRIX';
    modal.style.display = 'block';
}

function closeEnhanceDataTypeModal() {
    const modal = document.getElementById('enhanceDataTypeModal');
    if (modal) modal.style.display = 'none';
}

function confirmEnhanceDataType() {
    const sel = document.getElementById('inspire-enhance-data-type');
    const dt = sel ? sel.value : 'MATRIX';
    inspirationState.enhanceDataType = (dt === 'VECTOR') ? 'VECTOR' : 'MATRIX';
    closeEnhanceDataTypeModal();
    const input = document.getElementById('inspire-idea-file');
    if (input) input.click();
}

function startEnhanceStream(taskId, totalFiles) {
    const outputDiv = document.getElementById('inspire-output');
    const streamEl = document.getElementById('inspire-enhance-stream');
    if (!streamEl) {
        outputDiv.innerHTML = '<pre id="inspire-enhance-stream" style="white-space: pre-wrap; margin: 0;"></pre>';
    }
    const target = document.getElementById('inspire-enhance-stream');

    const source = new EventSource(`/api/inspiration/stream-enhance/${taskId}`);
    let completed = 0;

    source.onmessage = (event) => {
        try {
            const payload = JSON.parse(event.data);
            if (payload && payload.type === 'file_done') {
                completed += 1;
                target.textContent += `\n✅ 已完成 ${completed}/${totalFiles}: ${payload.file || ''} (${payload.success ? '成功' : '失败'})\n`;
                outputDiv.scrollTop = outputDiv.scrollHeight;
                return;
            }
            if (payload && payload.line !== undefined) {
                const prefix = payload.file ? `[${payload.file}] ` : '';
                target.textContent += prefix + payload.line + '\n';
                outputDiv.scrollTop = outputDiv.scrollHeight;
            }
        } catch {
            target.textContent += event.data + '\n';
            outputDiv.scrollTop = outputDiv.scrollHeight;
        }
    };

    source.addEventListener('done', (event) => {
        let info = null;
        try {
            info = JSON.parse(event.data);
        } catch {
            info = { success: false };
        }
        const enhanceBtn = document.getElementById('inspire-enhance');
        const enhanceDlBtn = document.getElementById('inspire-enhance-download');
        if (enhanceBtn) {
            enhanceBtn.disabled = false;
            enhanceBtn.textContent = '增强历史生成模板';
        }
        if (enhanceDlBtn) {
            enhanceDlBtn.style.display = info && info.success ? 'inline-block' : 'none';
        }
        source.close();
    });

    source.addEventListener('error', () => {
        const enhanceBtn = document.getElementById('inspire-enhance');
        const enhanceDlBtn = document.getElementById('inspire-enhance-download');
        if (enhanceBtn) {
            enhanceBtn.disabled = false;
            enhanceBtn.textContent = '增强历史生成模板';
        }
        if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
        target.textContent += '\n⚠️ 日志流中断。\n';
        source.close();
    });
}

function downloadEnhanceZip() {
    if (!inspirationState.enhanceTaskId) return;
    window.location.href = `/api/inspiration/download-enhance/${inspirationState.enhanceTaskId}`;
}

function downloadInspirationResult() {
    if (!inspirationState.lastResult) return;
    
    const blob = new Blob([inspirationState.lastResult], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `alpha_inspiration_${inspirationState.selectedDataset}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function resetInspirationTask() {
    inspirationState.selectedDataset = null;
    inspirationState.selectedDatasetCategory = null;
    const display = document.getElementById('inspire-selected-dataset');
    if (display) {
        display.textContent = "";
        display.style.display = 'none';
    }
    document.getElementById('inspire-output').innerHTML = "";
    document.getElementById('inspire-dataset-results').innerHTML = "";
    
    const dlBtn = document.getElementById('inspire-download');
    if (dlBtn) dlBtn.style.display = 'none';

    const directDlBtn = document.getElementById('inspire-direct-download');
    if (directDlBtn) directDlBtn.style.display = 'none';

    const enhanceDlBtn = document.getElementById('inspire-enhance-download');
    if (enhanceDlBtn) enhanceDlBtn.style.display = 'none';
    inspirationState.enhanceTaskId = null;

    if (inspirationState.pipelineEventSource) {
        inspirationState.pipelineEventSource.close();
        inspirationState.pipelineEventSource = null;
    }
    inspirationState.pipelineTaskId = null;
    
    const newTaskBtn = document.getElementById('inspire-new-task');
    if (newTaskBtn) {
        newTaskBtn.disabled = true;
        newTaskBtn.style.opacity = '0.5';
        newTaskBtn.style.cursor = 'not-allowed';
    }
    // Keep LLM config and Region/Universe selections
}

function toggleInspireColumn(colId) {
    const col = document.getElementById(colId);
    if (col) {
        col.classList.toggle('collapsed');
    }
}
