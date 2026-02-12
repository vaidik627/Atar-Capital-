document.addEventListener('DOMContentLoaded', () => {
    // --- State Management ---
    const state = {
        isAuthenticated: false,
        user: null,
        currentView: 'dashboard',
        currentDealId: null
    };

    // --- DOM Elements ---
    const authContainer = document.getElementById('auth-container');
    const appContainer = document.getElementById('app-container');
    const authForm = document.getElementById('auth-form');
    const authBtn = document.getElementById('auth-btn');
    const toggleAuth = document.getElementById('toggle-auth');
    const toggleText = document.getElementById('toggle-text');
    const authSubtitle = document.getElementById('auth-subtitle');
    const emailInput = document.getElementById('email');
    const logoutBtn = document.getElementById('logout-btn');
    const displayName = document.getElementById('display-name');
    const userInitials = document.getElementById('user-initials');
    const navItems = document.querySelectorAll('.nav-item');
    const pageTitle = document.getElementById('page-title');
    const contentArea = document.getElementById('content-area');

    // --- Authentication Logic ---

    // Toggle between Login and Signup (Visual only for now)
    let isLogin = true;
    toggleAuth.addEventListener('click', (e) => {
        e.preventDefault();
        isLogin = !isLogin;
        if (isLogin) {
            authSubtitle.textContent = 'Welcome back! Please login to your account.';
            authBtn.textContent = 'Sign In';
            toggleText.innerHTML = 'Don\'t have an account? <a href="#" id="toggle-auth">Sign Up</a>';
        } else {
            authSubtitle.textContent = 'Create an account to get started.';
            authBtn.textContent = 'Create Account';
            toggleText.innerHTML = 'Already have an account? <a href="#" id="toggle-auth">Sign In</a>';
        }
        // Re-attach event listener since innerHTML replaced the element
        document.getElementById('toggle-auth').addEventListener('click', arguments.callee);
    });

    // Handle Auth Form Submit
    authForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = emailInput.value;
        
        // Mock Login
        state.isAuthenticated = true;
        state.user = {
            email: email,
            name: email.split('@')[0].charAt(0).toUpperCase() + email.split('@')[0].slice(1) // Capitalize part before @
        };

        // Update UI
        updateUserProfile();
        showApp();
    });

    // Handle Logout
    logoutBtn.addEventListener('click', () => {
        state.isAuthenticated = false;
        state.user = null;
        showAuth();
        emailInput.value = '';
    });

    function updateUserProfile() {
        if (state.user) {
            displayName.textContent = state.user.name;
            userInitials.textContent = state.user.name.substring(0, 2).toUpperCase();
        }
    }

    function showApp() {
        authContainer.classList.add('hidden');
        appContainer.classList.remove('hidden');
        renderView('dashboard'); // Default view
    }

    function showAuth() {
        appContainer.classList.add('hidden');
        authContainer.classList.remove('hidden');
    }

    // --- Navigation Logic ---

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Update Active State
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Get View Name
            const viewName = item.getAttribute('data-view');
            renderView(viewName);
        });
    });

    // --- View Rendering (Mock Structure) ---

    function renderView(viewName) {
        state.currentView = viewName;
        
        // Update Header
        const titles = {
            'dashboard': 'Dashboard',
            'upload': 'Upload Document',
            'active-deals': 'Active Deals',
            'analysis': 'Deal Analysis',
            'reports': 'Reports',
            'settings': 'Settings'
        };
        pageTitle.textContent = titles[viewName] || 'Dashboard';

        // Render Content
        let html = '';
        switch(viewName) {
            case 'dashboard':
                html = `
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                        <div class="card">
                            <h3>Active Deals</h3>
                            <div style="height: 100px; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                                No active deals
                            </div>
                        </div>
                        <div class="card">
                            <h3>Recent Activity</h3>
                            <div style="height: 100px; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                                No recent activity
                            </div>
                        </div>
                        <div class="card">
                            <h3>System Status</h3>
                            <div style="height: 100px; display: flex; align-items: center; justify-content: center; color: #10b981;">
                                <i class="fas fa-check-circle" style="margin-right: 8px;"></i> All systems operational
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'upload':
                html = `
                    <div class="card" style="max-width: 800px; margin: 0 auto; padding: 2rem;">
                        <h3 style="margin-bottom: 1.5rem; text-align: center;">Upload New Deal</h3>
                        
                        <div class="form-group" style="margin-bottom: 1.5rem;">
                            <label style="display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--text-secondary);">Deal Name</label>
                            <input type="text" id="deal-name-input" placeholder="e.g. Project Manta Ray" class="input-wrapper" style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px;">
                        </div>

                        <div class="form-group" style="margin-bottom: 2rem;">
                            <label style="display: block; margin-bottom: 0.5rem; font-weight: 500; color: var(--text-secondary);">Deal Value</label>
                            <input type="text" id="deal-value-input" placeholder="e.g. $50M" class="input-wrapper" style="width: 100%; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: 6px;">
                        </div>

                        <div id="drop-zone" style="border: 2px dashed var(--border-color); border-radius: 8px; padding: 3rem; text-align: center; cursor: pointer; transition: all 0.2s; background: #f8fafc;">
                            <i class="fas fa-cloud-upload-alt" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 1rem;"></i>
                            <p style="color: #64748b; margin-bottom: 0.5rem;">Drag and drop PDF files here or click to browse</p>
                            <span class="btn-secondary" style="pointer-events: none;">Select File</span>
                            <input type="file" id="file-input" accept=".pdf" style="display: none;">
                        </div>
                        
                        <div id="file-preview" style="margin-top: 1.5rem; display: none; align-items: center; justify-content: space-between; padding: 1rem; background: #fff; border: 1px solid var(--border-color); border-radius: 6px;">
                            <div style="display: flex; align-items: center; gap: 1rem;">
                                <i class="fas fa-file-pdf" style="color: #ef4444; font-size: 1.5rem;"></i>
                                <span id="file-name" style="font-weight: 500;">filename.pdf</span>
                            </div>
                            <button id="remove-file" style="background: none; border: none; color: #94a3b8; cursor: pointer;"><i class="fas fa-times"></i></button>
                        </div>

                        <div id="upload-status" style="margin-top: 1.5rem; display: none;">
                            <div class="spinner" style="margin-bottom: 0.5rem;"><i class="fas fa-spinner fa-spin"></i> Processing...</div>
                            <div class="status-text">Uploading and extracting data...</div>
                        </div>

                        <button id="upload-submit-btn" class="btn-primary" style="width: 100%; margin-top: 2rem;" disabled>Upload & Analyze</button>
                    </div>
                `;
                break;
            case 'active-deals':
                html = `
                    <div class="card">
                        <div class="section-header">
                            <h3>Active Deals</h3>
                            <button class="btn-secondary" onclick="document.querySelector('[data-view=\\'upload\\']').click()"><i class="fas fa-plus"></i> New Deal</button>
                        </div>
                        <div id="deals-list-container">
                             <div style="padding: 3rem; text-align: center; color: #94a3b8;">
                                <i class="fas fa-spinner fa-spin"></i> Loading deals...
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'analysis':
                html = `
                    <div style="margin-bottom: 1.5rem; display: flex; align-items: center; justify-content: space-between;">
                         <div style="display: flex; align-items: center; gap: 1rem;">
                            <label style="font-weight: 500; color: var(--text-secondary);">Select Deal:</label>
                            <select id="deal-selector" style="padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 6px; min-width: 250px;">
                                <option value="">-- Select a Deal --</option>
                            </select>
                         </div>
                         <div id="deals-count-badge" class="badge" style="background: var(--primary-color); color: white; padding: 0.5rem 1rem;">
                            0 Deals Uploaded
                         </div>
                    </div>

                    <div id="analysis-content">
                        <div class="card">
                            <div class="empty-state" style="padding: 4rem;">
                                <div style="text-align: center;">
                                    ${state.currentDealId ? 
                                        `<i class="fas fa-spinner fa-spin" style="font-size: 3rem; color: var(--secondary-color); margin-bottom: 1rem;"></i>
                                         <p>Loading analysis data...</p>` : 
                                        `<i class="fas fa-chart-line" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 1rem;"></i>
                                         <p>Select a deal to view detailed analysis</p>`
                                    }
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                break;
            case 'reports':
                html = `
                    <div class="card">
                         <div class="section-header">
                            <h3>Generated Reports</h3>
                        </div>
                        <div class="empty-state" style="padding: 3rem;">
                            <p>No reports generated yet</p>
                        </div>
                    </div>
                `;
                break;
            case 'settings':
                html = `
                    <div class="card" style="max-width: 600px;">
                        <h3>Account Settings</h3>
                        <div style="margin-top: 2rem;">
                            <div class="form-group">
                                <label>Display Name</label>
                                <input type="text" class="input-wrapper" style="width: 100%; padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 4px;" value="${state.user ? state.user.name : ''}" disabled>
                            </div>
                            <div class="form-group">
                                <label>Email Address</label>
                                <input type="email" class="input-wrapper" style="width: 100%; padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 4px;" value="${state.user ? state.user.email : ''}" disabled>
                            </div>
                        </div>
                    </div>
                `;
                break;
            default:
                html = '<div class="empty-state"><p>View not found</p></div>';
        }

        contentArea.innerHTML = html;

        function renderProfitRow(label, data, isRevenue = false) {
            let content = '';
            
            if (isRevenue && data) {
                // Handle single revenue object
                const val = data.value || '-';
                const unit = data.unit || '';
                const per = data.period || '';
                content = `
                    <div style="text-align: right;">
                        <div style="font-weight: 600;">${val} ${unit}</div>
                        ${per ? `<div style="font-size: 0.75rem; color: #94a3b8;">${per}</div>` : ''}
                    </div>
                `;
            } else if (Array.isArray(data) && data.length > 0) {
                // Handle array of profit metrics
                content = `
                    <div style="text-align: right; display: flex; flex-direction: column; gap: 4px;">
                        ${data.map(item => `
                            <div>
                                <span style="font-weight: 600;">${item.value || '-'} ${item.unit || ''}</span>
                                <span style="font-size: 0.75rem; color: #94a3b8; margin-left: 6px;">(${item.period || 'N/A'})</span>
                            </div>
                        `).join('')}
                    </div>
                `;
            } else {
                return ''; // Don't render empty rows
            }

            return `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; padding: 0.5rem 0; border-bottom: 1px solid #f8fafc; font-size: 0.9rem;">
                    <span style="color: var(--text-secondary); margin-top: 2px;">${label}</span>
                    ${content}
                </div>
            `;
        }

        function renderMarginCard(label, data, color) {
            if (!Array.isArray(data) || data.length === 0) return '';
            
            const latest = data[0];
            const value = latest.value;
            if (!value) return '';

            return `
                <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid ${color};">
                    <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 0.25rem;">${label}</div>
                    <div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">
                        ${value}%
                    </div>
                    <div style="font-size: 0.75rem; color: #94a3b8;">${latest.period || 'Latest'}</div>
                </div>
            `;
        }

        // Attach event listeners for specific views
        if (viewName === 'analysis' && state.currentDealId) {
            loadAnalysisData(state.currentDealId);
        }



        function renderAnalysisDashboard(data) {
            const container = document.getElementById('analysis-content');
            
            // Helper to format numbers safely
            const fmt = (val) => val !== undefined && val !== null ? val : 'N/A';
            
            let html = `
                <div style="display: flex; flex-direction: column; gap: 1.5rem;">
                    
                    <!-- Header Section -->
                    <div class="card" style="border-left: 4px solid var(--secondary-color);">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <h2 style="margin: 0; color: var(--primary-color);">${fmt(data.header.companyName)}</h2>
                                <p style="color: var(--text-secondary); margin-top: 0.5rem;">
                                    Currency: <span style="font-weight: 600;">${fmt(data.header.currency)}</span>
                                </p>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 0.875rem; color: var(--text-secondary);">Market Size / Deal Value</div>
                                <div style="font-size: 1.5rem; font-weight: 700; color: var(--success-color);">
                                    ${fmt(data.header.dealValue.display)}
                                </div>
                            </div>
                        </div>
                        <div style="margin-top: 1.5rem; background: #f8fafc; padding: 1rem; border-radius: 8px;">
                            <h4 style="margin-top: 0; font-size: 0.9rem; color: var(--text-secondary);">EXECUTIVE SUMMARY</h4>
                            <p style="margin-bottom: 0; line-height: 1.6;">${fmt(data.summary.text)}</p>
                        </div>
                    </div>

                    <!-- AI Suggestion -->
                    <div class="card" style="background: linear-gradient(to right, #f0f9ff, #e0f2fe); border: 1px solid #bae6fd;">
                        <div style="display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem;">
                            <div style="background: var(--secondary-color); color: white; width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center;">
                                <i class="fas fa-robot"></i>
                            </div>
                            <div>
                                <h3 style="margin: 0;">AI Recommendation</h3>
                                <span style="font-size: 0.875rem; color: var(--text-secondary);">Confidence: ${fmt(data.aiSuggestion.confidence)}%</span>
                            </div>
                        </div>
                        <div style="font-size: 1.25rem; font-weight: 600; color: var(--primary-color); margin-bottom: 0.5rem;">
                            ${fmt(data.aiSuggestion.recommendation)}
                        </div>
                        <p style="margin: 0;">${fmt(data.aiSuggestion.rationale)}</p>
                    </div>

                    <!-- Financials Grid -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem;">
                        
                        <!-- Revenue Analysis -->
                        <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-money-bill-wave" style="color: var(--success-color); margin-right: 0.5rem;"></i> Revenue Analysis
                            </h3>
                            
                            <div style="display: flex; justify-content: space-between; margin-bottom: 1.5rem;">
                                <div>
                                    <div style="font-size: 0.875rem; color: var(--text-secondary);">Present Revenue</div>
                                    <div style="font-size: 1.25rem; font-weight: 600;">${fmt(data.revenue.present.value)} (${fmt(data.revenue.present.period)})</div>
                                </div>
                            </div>

                            <table style="width: 100%; font-size: 0.9rem;">
                                <thead>
                                    <tr style="text-align: left; color: var(--text-secondary);">
                                        <th style="padding-bottom: 0.5rem;">Period</th>
                                        <th style="padding-bottom: 0.5rem;">Revenue</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${(data.revenue.history || []).map(h => `
                                        <tr>
                                            <td style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9;">${h.period}</td>
                                            <td style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9; font-weight: 500;">${h.value} ${h.unit || ''}</td>
                                        </tr>
                                    `).join('')}
                                    ${(data.revenue.future || []).map(f => `
                                        <tr style="color: var(--text-secondary);">
                                            <td style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9;">${f.period} (E)</td>
                                            <td style="padding: 0.5rem 0; border-top: 1px solid #f1f5f9;">${f.value} ${f.unit || ''}</td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>

                        <!-- Profitability -->
                        <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-chart-pie" style="color: var(--warning-color); margin-right: 0.5rem;"></i> Profitability
                            </h3>
                            
                            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 1.5rem;">
                                <!-- Profitability & Margins -->
                                <div>
                                    <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em;">Core Profitability</h4>
                                    
                                    <div style="margin-bottom: 1rem;">
                                        <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 600; padding-bottom: 0.25rem; border-bottom: 1px solid #e2e8f0; margin-bottom: 0.5rem;">
                                        <span>Metric</span>
                                        <span>Values (Period)</span>
                                    </div>
                                        
                                        ${renderProfitRow('Revenue', data.revenue?.present, true)}
                                        ${renderProfitRow('Gross Profit', data.profitMetrics?.gross_profit)}
                                        ${renderProfitRow('EBITDA', data.profitMetrics?.ebitda)}
                                        ${renderProfitRow('Adj. EBITDA', data.profitMetrics?.adjusted_ebitda)}
                                        ${renderProfitRow('Op. Income', data.profitMetrics?.operating_income)}
                                        ${renderProfitRow('Net Income', data.profitMetrics?.net_income)}
                                        ${renderProfitRow('Op. Cash Flow', data.profitMetrics?.operating_cash_flow)}
                                    </div>
                                </div>

                                <!-- Key Margins -->
                                <div>
                                    <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.05em;">Key Margins & Ratios</h4>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                                        ${renderMarginCard('Gross Margin', data.profitMetrics?.gross_margin_percent, '#10b981')}
                                        ${renderMarginCard('EBITDA Margin', data.profitMetrics?.ebitda_margin_percent, '#f59e0b')}
                                        ${renderMarginCard('Op. Margin', data.profitMetrics?.operating_margin_percent, '#3b82f6')}
                                        ${renderMarginCard('Net Margin', data.profitMetrics?.net_margin_percent, '#6366f1')}
                                    </div>
                                </div>
                            </div>
                        </div>

                    </div>

                    <!-- Risks & Market -->
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 1.5rem;">
                        
                        <!-- Risk Analysis -->
                        <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-exclamation-triangle" style="color: var(--danger-color); margin-right: 0.5rem;"></i> Risk Analysis
                            </h3>
                            
                            <div style="display: flex; flex-direction: column; gap: 1rem;">
                                ${data.riskAnalysis.operational.length > 0 ? `
                                    <div>
                                        <span class="badge" style="background: #fee2e2; color: #991b1b; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">OPERATIONAL</span>
                                        <ul style="margin: 0.5rem 0 0 1.25rem; color: var(--text-primary);">
                                            ${data.riskAnalysis.operational.map(r => `<li>${r}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                                
                                ${data.riskAnalysis.financial.length > 0 ? `
                                    <div>
                                        <span class="badge" style="background: #ffedd5; color: #9a3412; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">FINANCIAL</span>
                                        <ul style="margin: 0.5rem 0 0 1.25rem; color: var(--text-primary);">
                                            ${data.riskAnalysis.financial.map(r => `<li>${r}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}

                                ${data.riskAnalysis.market && data.riskAnalysis.market.length > 0 ? `
                                    <div>
                                        <span class="badge" style="background: #e0f2fe; color: #075985; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">MARKET</span>
                                        <ul style="margin: 0.5rem 0 0 1.25rem; color: var(--text-primary);">
                                            ${data.riskAnalysis.market.map(r => `<li>${r}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}

                                ${data.riskAnalysis.regulatory && data.riskAnalysis.regulatory.length > 0 ? `
                                    <div>
                                        <span class="badge" style="background: #f3e8ff; color: #6b21a8; padding: 0.25rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">REGULATORY</span>
                                        <ul style="margin: 0.5rem 0 0 1.25rem; color: var(--text-primary);">
                                            ${data.riskAnalysis.regulatory.map(r => `<li>${r}</li>`).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                            </div>
                        </div>

                        <!-- Market Intelligence -->
                        <div class="card">
                            <h3 style="border-bottom: 1px solid var(--border-color); padding-bottom: 0.75rem; margin-bottom: 1rem;">
                                <i class="fas fa-globe" style="color: var(--secondary-color); margin-right: 0.5rem;"></i> Market Intelligence
                            </h3>
                            
                            <p><strong>Industry Position:</strong> ${fmt(data.marketIntelligence.industryPosition)}</p>
                            <p><strong>Market Share:</strong> ${fmt(data.marketIntelligence.marketSharePercent)}</p>
                            
                            <h4 style="font-size: 0.9rem; margin-top: 1.5rem;">Key Competitors</h4>
                            <div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                                ${(data.marketIntelligence.competitors || []).map(c => `
                                    <span style="background: #f1f5f9; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.875rem;">${c}</span>
                                `).join('')}
                                ${(!data.marketIntelligence.competitors || data.marketIntelligence.competitors.length === 0) ? '<span style="color: #94a3b8;">No competitor data</span>' : ''}
                            </div>
                        </div>

                    </div>
                </div>
            `;
            
            container.innerHTML = html;
        }

        // Attach event listeners for specific views
        if (viewName === 'upload') {
            const dropZone = document.getElementById('drop-zone');
            const fileInput = document.getElementById('file-input');
            const filePreview = document.getElementById('file-preview');
            const fileNameSpan = document.getElementById('file-name');
            const removeFileBtn = document.getElementById('remove-file');
            const uploadBtn = document.getElementById('upload-submit-btn');
            const dealNameInput = document.getElementById('deal-name-input');
            const dealValueInput = document.getElementById('deal-value-input');
            const uploadStatus = document.getElementById('upload-status');
            const statusText = uploadStatus.querySelector('.status-text');

            let selectedFile = null;

            dropZone.addEventListener('click', () => fileInput.click());

            fileInput.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    handleFileSelection(e.target.files[0]);
                }
            });

            // Drag and drop handlers
            dropZone.addEventListener('dragover', (e) => {
                e.preventDefault();
                dropZone.style.background = '#f1f5f9';
                dropZone.style.borderColor = 'var(--primary-color)';
            });

            dropZone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                dropZone.style.background = '#f8fafc';
                dropZone.style.borderColor = 'var(--border-color)';
            });

            dropZone.addEventListener('drop', (e) => {
                e.preventDefault();
                dropZone.style.background = '#f8fafc';
                dropZone.style.borderColor = 'var(--border-color)';
                
                if (e.dataTransfer.files.length > 0) {
                    handleFileSelection(e.dataTransfer.files[0]);
                }
            });

            function handleFileSelection(file) {
                if (file.type !== 'application/pdf') {
                    alert('Please select a PDF file.');
                    return;
                }
                selectedFile = file;
                fileNameSpan.textContent = file.name;
                dropZone.style.display = 'none';
                filePreview.style.display = 'flex';
                validateForm();
            }

            removeFileBtn.addEventListener('click', () => {
                selectedFile = null;
                fileInput.value = '';
                filePreview.style.display = 'none';
                dropZone.style.display = 'block';
                validateForm();
            });

            [dealNameInput, dealValueInput].forEach(input => {
                input.addEventListener('input', validateForm);
            });

            function validateForm() {
                const isValid = selectedFile && dealNameInput.value.trim() && dealValueInput.value.trim();
                uploadBtn.disabled = !isValid;
                uploadBtn.style.opacity = isValid ? '1' : '0.5';
            }

            uploadBtn.addEventListener('click', async () => {
                if (!selectedFile) return;
                await uploadFile(selectedFile);
            });

            async function uploadFile(file) {
                // Show loading state
                uploadBtn.disabled = true;
                uploadBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
                uploadStatus.style.display = 'block';
                statusText.textContent = `Uploading ${file.name} and extracting data...`;

                const formData = new FormData();
                formData.append('document', file);
                formData.append('dealName', dealNameInput.value.trim());
                formData.append('dealValue', dealValueInput.value.trim());

                try {
                    const response = await fetch('http://localhost:8000/api/documents/upload', {
                        method: 'POST',
                        body: formData
                    });

                    if (!response.ok) {
                        throw new Error(`Upload failed: ${response.statusText}`);
                    }

                    const result = await response.json();
                    
                    if (result.success) {
                        statusText.textContent = 'Upload complete! OCR processing finished.';
                        statusText.style.color = '#10b981';
                        
                        // Store deal ID and redirect to analysis
                        state.currentDealId = result.dealId;
                        
                        setTimeout(() => {
                            alert('Document uploaded and processed successfully! Redirecting to analysis...');
                            document.querySelector('[data-view="analysis"]').click();
                        }, 1000);
                    } else {
                        throw new Error(result.message || 'Unknown error occurred');
                    }

                } catch (error) {
                    console.error('Error:', error);
                    statusText.textContent = `Error: ${error.message}`;
                    statusText.style.color = '#ef4444';
                    uploadBtn.disabled = false;
                    uploadBtn.innerHTML = 'Retry Upload';
                }
            }
        }

        if (viewName === 'active-deals') {
            loadActiveDeals();
        }

        async function loadActiveDeals() {
            try {
                const response = await fetch('http://localhost:8000/api/deals');
                const result = await response.json();
                const container = document.getElementById('deals-list-container');

                if (result.success && result.deals && result.deals.length > 0) {
                    container.innerHTML = `
                        <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
                            ${result.deals.map(deal => `
                                <div class="card" style="transition: transform 0.2s; cursor: pointer;" onclick="window.loadDealAnalysis('${deal.id}')">
                                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1rem;">
                                        <div style="width: 40px; height: 40px; background: #e0f2fe; color: var(--primary-color); border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: bold;">
                                            ${deal.name.substring(0, 2).toUpperCase()}
                                        </div>
                                        <span class="badge" style="background: #dcfce7; color: #166534; padding: 0.25rem 0.5rem; border-radius: 99px; font-size: 0.75rem;">${deal.status}</span>
                                    </div>
                                    <h3 style="margin-bottom: 0.5rem; font-size: 1.1rem;">${deal.name}</h3>
                                    <p style="color: var(--text-secondary); margin-bottom: 1rem; font-size: 0.9rem;">
                                        <i class="fas fa-tag" style="margin-right: 0.5rem;"></i> ${deal.value}
                                    </p>
                                    <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #f1f5f9; padding-top: 1rem; font-size: 0.875rem; color: #94a3b8;">
                                        <span><i class="far fa-calendar-alt"></i> ${deal.date}</span>
                                        <span style="color: var(--primary-color); font-weight: 500;">View Analysis &rarr;</span>
                                    </div>
                                </div>
                            `).join('')}
                        </div>
                    `;
                } else {
                    container.innerHTML = `
                        <div style="text-align: center; padding: 3rem; color: #94a3b8;">
                            <i class="fas fa-folder-open" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                            <p>No active deals found. Upload a document to create a new deal.</p>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading deals:', error);
                document.getElementById('deals-list-container').innerHTML = `<p style="color: #ef4444; text-align: center;">Error loading deals.</p>`;
            }
        }

        // Global helper for deal click
        window.loadDealAnalysis = (dealId) => {
             state.currentDealId = dealId;
             document.querySelector('[data-view="analysis"]').click();
        };

        if (viewName === 'analysis') {
             loadDealsForSelector();
             if (state.currentDealId) {
                 loadAnalysisData(state.currentDealId);
             }
        }

        async function loadDealsForSelector() {
            try {
                const response = await fetch('http://localhost:8000/api/deals');
                const result = await response.json();
                const selector = document.getElementById('deal-selector');
                const badge = document.getElementById('deals-count-badge');

                if (result.success && result.deals) {
                    badge.textContent = `${result.deals.length} Deals Uploaded`;
                    
                    selector.innerHTML = '<option value="">-- Select a Deal --</option>' + 
                        result.deals.map(deal => `<option value="${deal.id}" ${state.currentDealId === deal.id ? 'selected' : ''}>${deal.name}</option>`).join('');
                    
                    selector.addEventListener('change', (e) => {
                        const dealId = e.target.value;
                        if (dealId) {
                            state.currentDealId = dealId;
                            loadAnalysisData(dealId);
                        } else {
                            state.currentDealId = null;
                            document.getElementById('analysis-content').innerHTML = `
                                <div class="card"><div class="empty-state" style="padding: 4rem; text-align: center;">
                                    <i class="fas fa-chart-line" style="font-size: 3rem; color: #cbd5e1; margin-bottom: 1rem;"></i>
                                    <p>Select a deal to view detailed analysis</p>
                                </div></div>`;
                        }
                    });
                }
            } catch (e) {
                console.error("Error loading deals for selector", e);
            }
        }

        async function loadAnalysisData(dealId) {
            const container = document.getElementById('analysis-content');
            container.innerHTML = `
                <div class="card">
                    <div class="empty-state" style="padding: 4rem; text-align: center;">
                         <i class="fas fa-spinner fa-spin" style="font-size: 3rem; color: var(--secondary-color); margin-bottom: 1rem;"></i>
                         <p>Loading analysis data...</p>
                    </div>
                </div>
            `;

            try {
                const response = await fetch(`http://localhost:8000/api/analysis/${dealId}`);
                const result = await response.json();

                if (result.success && result.data && Object.keys(result.data).length > 0) {
                    renderAnalysisDashboard(result.data);
                } else {
                    container.innerHTML = `
                        <div class="card">
                            <div class="empty-state" style="padding: 4rem; text-align: center;">
                                <i class="fas fa-exclamation-circle" style="font-size: 3rem; color: #ef4444; margin-bottom: 1rem;"></i>
                                <p>Analysis data not found or still processing.</p>
                                <button class="btn-secondary" onclick="loadAnalysisData('${dealId}')" style="margin-top: 1rem;">Retry</button>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error fetching analysis:', error);
                container.innerHTML = `
                     <div class="card">
                        <p style="color: #ef4444;">Error loading analysis: ${error.message}</p>
                    </div>
                `;
            }
        }
    }
});
