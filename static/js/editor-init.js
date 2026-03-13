/**
 * Shared Editor.js initialization utility for Vibing.
 * 
 * Usage:
 *   initVibingEditor({
 *       holderId: 'editorjs',
 *       initialData: { blocks: [...] },
 *       wsUrl: 'ws://localhost:8000/ws/project/1/',
 *       wsMessageType: 'project_update',
 *       statusElementId: 'editor-status',
 *       csrfToken: '...'  // needed for image upload
 *   });
 */
function initVibingEditor(config) {
    const {
        holderId,
        initialData,
        wsUrl,
        wsMessageType,
        statusElementId,
        placeholder,
        csrfToken,
        readOnly
    } = config;

    let isEditing = false;
    let saveTimeout = null;
    const statusEl = statusElementId ? document.getElementById(statusElementId) : null;

    function setStatus(text) {
        if (statusEl) statusEl.textContent = text;
    }

    // Build tools config from globals exposed by CDN scripts
    // Note: some plugin versions register under different global names
    const tools = {};
    
    const HeaderClass = window.Header || window.EditorjsHeader;
    const ListClass = window.EditorjsList || window.List;
    const ChecklistClass = window.Checklist || window.EditorjsChecklist;
    const TableClass = window.Table || window.EditorjsTable;
    const CodeClass = window.CodeTool || window.EditorjsCodeTool;
    const QuoteClass = window.Quote || window.EditorjsQuote;
    const DelimiterClass = window.Delimiter || window.EditorjsDelimiter;
    const WarningClass = window.Warning || window.EditorjsWarning;
    const ImageClass = window.ImageTool || window.EditorjsImageTool;

    if (HeaderClass) tools.header = {
        class: HeaderClass,
        config: { levels: [1, 2, 3, 4], defaultLevel: 2 }
    };
    if (ListClass) tools.list = { class: ListClass, inlineToolbar: true };
    if (ChecklistClass) tools.checklist = { class: ChecklistClass, inlineToolbar: true };
    if (TableClass) tools.table = { class: TableClass, inlineToolbar: true };
    if (CodeClass) tools.code = CodeClass;
    if (QuoteClass) tools.quote = { class: QuoteClass, inlineToolbar: true };
    if (DelimiterClass) tools.delimiter = DelimiterClass;
    if (WarningClass) tools.warning = { class: WarningClass, inlineToolbar: true };
    if (ImageClass) {
        tools.image = {
            class: ImageClass,
            config: {
                endpoints: {
                    byFile: '/api/upload/image/'
                },
                additionalRequestHeaders: csrfToken ? { 'X-CSRFToken': csrfToken } : {}
            }
        };
    }

    console.log('[Vibing Editor] Detected tools:', Object.keys(tools).join(', ') || 'none');

    // Validate data: only pass if it has blocks
    const hasData = initialData && initialData.blocks && initialData.blocks.length > 0;

    const editorConfig = {
        holder: holderId,
        data: hasData ? initialData : undefined,
        placeholder: placeholder || 'Start writing here...',
        tools: tools,
        readOnly: readOnly || false,
        onReady: () => {
            setStatus(readOnly ? 'Read-only' : 'Editor ready');
        },
    };

    if (!readOnly) {
        editorConfig.onChange = (api, event) => {
            isEditing = true;
            clearTimeout(saveTimeout);
            setStatus('Saving...');
            saveTimeout = setTimeout(() => {
                editor.save().then((outputData) => {
                    if (socket && socket.readyState === WebSocket.OPEN) {
                        socket.send(JSON.stringify({
                            type: wsMessageType,
                            payload: outputData
                        }));
                        setStatus('Saved ✓');
                    }
                    setTimeout(() => { isEditing = false; }, 500);
                }).catch((err) => {
                    console.error('Editor save error:', err);
                    setStatus('Save error');
                });
            }, 600);
        };
    }

    const editor = new EditorJS(editorConfig);

    // WebSocket for real-time collaboration
    const socket = new WebSocket(wsUrl);

    socket.onopen = () => {
        console.log('WebSocket connected for editor sync');
    };

    socket.onmessage = function(e) {
        const data = JSON.parse(e.data);
        if (data.type === wsMessageType && !isEditing) {
            editor.isReady.then(() => {
                editor.render(data.payload);
                setStatus('Updated from collaborator');
            });
        }
    };

    socket.onerror = (err) => {
        console.warn('WebSocket error:', err);
        setStatus('Connection error — changes saved locally');
    };

    socket.onclose = () => {
        console.log('WebSocket closed');
    };

    return { editor, socket };
}
