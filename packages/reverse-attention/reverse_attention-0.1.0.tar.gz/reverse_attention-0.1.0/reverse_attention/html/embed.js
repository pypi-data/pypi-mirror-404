// Reverse Attention Sankey Visualization
// Interactive D3.js visualization for attention beam paths

(function() {
    'use strict';

    // Global state
    let traceData = null;
    let svg = null;
    let g = null;
    let zoom = null;
    let selectedBeam = null;
    let highlightedNodes = new Set();

    // Color scale for beams
    const beamColors = d3.scaleOrdinal()
        .domain(d3.range(10))
        .range([
            '#e94560', '#4cc9f0', '#f72585', '#7209b7', '#3a0ca3',
            '#4361ee', '#4895ef', '#560bad', '#480ca8', '#b5179e'
        ]);

    // Initialize visualization
    async function init() {
        try {
            // Load trace data
            const response = await fetch('trace.json');
            traceData = await response.json();

            // Set up UI
            setupMetadataPanel();
            setupBeamList();
            setupBeamFilter();
            setupControls();

            // Create visualization
            createSankey();
        } catch (error) {
            console.error('Failed to load trace data:', error);
            document.getElementById('sankey-container').innerHTML =
                '<div style="padding: 2rem; color: #e94560;">Error loading trace data. Make sure trace.json exists.</div>';
        }
    }

    function setupMetadataPanel() {
        const container = document.getElementById('metadata-info');
        const meta = traceData.metadata;

        container.innerHTML = `
            <div class="info-item">
                <span>Sequence Length</span>
                <span class="value">${meta.seq_len}</span>
            </div>
            <div class="info-item">
                <span>Target Position</span>
                <span class="value">${meta.target_pos}</span>
            </div>
            <div class="info-item">
                <span>Layer</span>
                <span class="value">${meta.layer}</span>
            </div>
            <div class="info-item">
                <span>Top Beams</span>
                <span class="value">${meta.top_beam}</span>
            </div>
            <div class="info-item">
                <span>Top K</span>
                <span class="value">${meta.top_k}</span>
            </div>
        `;
    }

    function setupBeamList() {
        const container = document.getElementById('beam-list');
        container.innerHTML = '';

        traceData.beams.forEach((beam, idx) => {
            const div = document.createElement('div');
            div.className = 'beam-item';
            div.dataset.beamIndex = idx;

            const pathText = traceData.paths_text[idx] || beam.tokens.slice().reverse().join(' -> ');

            div.innerHTML = `
                <div class="beam-header">
                    <span class="beam-index" style="color: ${beamColors(idx)}">Beam ${idx + 1}</span>
                    <span class="beam-score">${beam.score_norm.toFixed(4)}</span>
                </div>
                <div class="beam-path">${escapeHtml(pathText)}</div>
            `;

            div.addEventListener('click', () => selectBeam(idx));
            container.appendChild(div);
        });
    }

    function setupBeamFilter() {
        const select = document.getElementById('beam-filter');
        select.innerHTML = '<option value="all">All Beams</option>';

        traceData.beams.forEach((_, idx) => {
            const option = document.createElement('option');
            option.value = idx;
            option.textContent = `Beam ${idx + 1}`;
            option.style.color = beamColors(idx);
            select.appendChild(option);
        });

        select.addEventListener('change', (e) => {
            if (e.target.value === 'all') {
                selectedBeam = null;
                clearBeamSelection();
            } else {
                selectBeam(parseInt(e.target.value));
            }
            updateLinkVisibility();
        });
    }

    function setupControls() {
        document.getElementById('reset-zoom').addEventListener('click', resetZoom);
        document.getElementById('reset-highlight').addEventListener('click', () => {
            clearHighlight();
            selectedBeam = null;
            document.getElementById('beam-filter').value = 'all';
            clearBeamSelection();
            updateLinkVisibility();
        });
    }

    function createSankey() {
        const container = document.getElementById('sankey-container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        // Clear previous
        container.innerHTML = '';

        // Create SVG
        svg = d3.select(container)
            .append('svg')
            .attr('width', width)
            .attr('height', height);

        // Create group for zoom/pan
        g = svg.append('g');

        // Set up zoom behavior
        zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                g.attr('transform', event.transform);
            });

        svg.call(zoom);

        // Prepare Sankey data
        const sankeyData = prepareSankeyData();

        // Create Sankey generator
        const sankey = d3.sankey()
            .nodeId(d => d.id)
            .nodeWidth(20)
            .nodePadding(20)
            .nodeAlign(d3.sankeyLeft)
            .extent([[50, 50], [width - 50, height - 50]]);

        // Generate layout
        const { nodes, links } = sankey(sankeyData);

        // Draw links
        const linkGroup = g.append('g')
            .attr('class', 'links')
            .attr('fill', 'none');

        const link = linkGroup.selectAll('.link')
            .data(links)
            .enter()
            .append('path')
            .attr('class', 'link')
            .attr('d', d3.sankeyLinkHorizontal())
            .attr('stroke-width', d => Math.max(2, d.width))
            .attr('stroke', d => getLinkColor(d))
            .attr('data-beam-indices', d => d.beam_indices.join(','))
            .on('click', (event, d) => showLinkInfo(d))
            .on('mouseover', (event, d) => showTooltip(event, getLinkTooltip(d)))
            .on('mouseout', hideTooltip);

        // Draw nodes
        const nodeGroup = g.append('g')
            .attr('class', 'nodes');

        const node = nodeGroup.selectAll('.node')
            .data(nodes)
            .enter()
            .append('g')
            .attr('class', 'node')
            .attr('transform', d => `translate(${d.x0},${d.y0})`)
            .on('click', (event, d) => {
                event.stopPropagation();
                highlightConnected(d);
                showNodeInfo(d);
            })
            .on('mouseover', (event, d) => showTooltip(event, getNodeTooltip(d)))
            .on('mouseout', hideTooltip);

        node.append('rect')
            .attr('height', d => d.y1 - d.y0)
            .attr('width', sankey.nodeWidth())
            .attr('fill', d => getNodeColor(d));

        node.append('text')
            .attr('x', sankey.nodeWidth() + 6)
            .attr('y', d => (d.y1 - d.y0) / 2)
            .attr('dy', '0.35em')
            .attr('text-anchor', 'start')
            .text(d => truncateToken(d.name, 15))
            .filter(d => d.x0 > width / 2)
            .attr('x', -6)
            .attr('text-anchor', 'end');

        // Click on background to clear selection
        svg.on('click', () => {
            clearHighlight();
            clearClickInfo();
        });
    }

    function prepareSankeyData() {
        // Deep copy nodes and links
        const nodes = traceData.sankey.nodes.map(n => ({
            ...n,
            id: n.id
        }));

        const links = traceData.sankey.links.map(l => ({
            source: l.source,
            target: l.target,
            value: Math.max(l.value, 0.01), // Minimum value for visibility
            beam_indices: l.beam_indices
        }));

        return { nodes, links };
    }

    function getLinkColor(link) {
        if (link.beam_indices.length === 1) {
            return beamColors(link.beam_indices[0]);
        }
        // Mixed beams - use gradient or neutral color
        return '#888';
    }

    function getNodeColor(node) {
        // Color by position (gradient from start to end)
        const positions = traceData.sankey.nodes.map(n => n.position);
        const minPos = Math.min(...positions);
        const maxPos = Math.max(...positions);
        const t = (node.position - minPos) / (maxPos - minPos || 1);

        return d3.interpolateViridis(t);
    }

    function truncateToken(token, maxLen) {
        if (token.length <= maxLen) return token;
        return token.substring(0, maxLen - 1) + '...';
    }

    function highlightConnected(node) {
        clearHighlight();

        highlightedNodes.add(node.id);

        // Find connected links
        d3.selectAll('.link').each(function(d) {
            const linkEl = d3.select(this);
            if (d.source.id === node.id || d.target.id === node.id) {
                linkEl.classed('highlighted', true);
                highlightedNodes.add(d.source.id);
                highlightedNodes.add(d.target.id);
            } else {
                linkEl.classed('dimmed', true);
            }
        });

        // Highlight connected nodes
        d3.selectAll('.node').each(function(d) {
            if (!highlightedNodes.has(d.id)) {
                d3.select(this).style('opacity', 0.3);
            }
        });
    }

    function clearHighlight() {
        highlightedNodes.clear();
        d3.selectAll('.link')
            .classed('highlighted', false)
            .classed('dimmed', false);
        d3.selectAll('.node')
            .style('opacity', 1);
    }

    function selectBeam(beamIndex) {
        selectedBeam = beamIndex;

        // Update beam list selection
        document.querySelectorAll('.beam-item').forEach((el, idx) => {
            el.classList.toggle('selected', idx === beamIndex);
        });

        // Update filter dropdown
        document.getElementById('beam-filter').value = beamIndex;

        updateLinkVisibility();
    }

    function clearBeamSelection() {
        document.querySelectorAll('.beam-item').forEach(el => {
            el.classList.remove('selected');
        });
    }

    function updateLinkVisibility() {
        d3.selectAll('.link').each(function(d) {
            const linkEl = d3.select(this);
            if (selectedBeam === null) {
                linkEl.style('opacity', 1);
            } else {
                const visible = d.beam_indices.includes(selectedBeam);
                linkEl.style('opacity', visible ? 1 : 0.1);
            }
        });
    }

    function showNodeInfo(node) {
        const container = document.getElementById('click-info');
        const token = traceData.tokens[node.position];

        container.className = 'click-info';
        container.innerHTML = `
            <div class="info-item">
                <span>Type</span>
                <span class="value">Node</span>
            </div>
            <div class="info-item">
                <span>Position</span>
                <span class="value">${node.position}</span>
            </div>
            <div class="info-item">
                <span>Token</span>
                <span class="value">${escapeHtml(token)}</span>
            </div>
            <div class="info-item">
                <span>Token ID</span>
                <span class="value">${getTokenId(node.position)}</span>
            </div>
        `;
    }

    function showLinkInfo(link) {
        const container = document.getElementById('click-info');

        const sourceToken = traceData.tokens[link.source.position];
        const targetToken = traceData.tokens[link.target.position];

        container.className = 'click-info';
        container.innerHTML = `
            <div class="info-item">
                <span>Type</span>
                <span class="value">Link</span>
            </div>
            <div class="info-item">
                <span>From</span>
                <span class="value">${escapeHtml(sourceToken)} (${link.source.position})</span>
            </div>
            <div class="info-item">
                <span>To</span>
                <span class="value">${escapeHtml(targetToken)} (${link.target.position})</span>
            </div>
            <div class="info-item">
                <span>Attention</span>
                <span class="value">${link.value.toFixed(4)}</span>
            </div>
            <div class="info-item">
                <span>Beams</span>
                <span class="value">${link.beam_indices.map(i => i + 1).join(', ')}</span>
            </div>
        `;
    }

    function clearClickInfo() {
        const container = document.getElementById('click-info');
        container.className = 'click-info empty';
        container.innerHTML = 'Click a node or link for details';
    }

    function getTokenId(position) {
        // Find token ID from beams data
        for (const beam of traceData.beams) {
            const idx = beam.positions.indexOf(position);
            if (idx !== -1) {
                return beam.token_ids[idx];
            }
        }
        return 'N/A';
    }

    function showTooltip(event, content) {
        const tooltip = document.getElementById('tooltip');
        tooltip.innerHTML = content;
        tooltip.style.display = 'block';
        tooltip.style.left = (event.pageX + 10) + 'px';
        tooltip.style.top = (event.pageY + 10) + 'px';
    }

    function hideTooltip() {
        document.getElementById('tooltip').style.display = 'none';
    }

    function getNodeTooltip(node) {
        const token = traceData.tokens[node.position];
        return `<strong>Position ${node.position}</strong><br>${escapeHtml(token)}`;
    }

    function getLinkTooltip(link) {
        const sourceToken = traceData.tokens[link.source.position];
        const targetToken = traceData.tokens[link.target.position];
        return `<strong>${escapeHtml(sourceToken)} → ${escapeHtml(targetToken)}</strong><br>Attention: ${link.value.toFixed(4)}`;
    }

    function resetZoom() {
        svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity);
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Handle window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            if (traceData) {
                createSankey();
            }
        }, 250);
    });

    // Initialize on load
    document.addEventListener('DOMContentLoaded', init);
})();
