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
                    <div class="card" style="max-width: 800px; margin: 0 auto; text-align: center; padding: 4rem 2rem;">
                        <i class="fas fa-cloud-upload-alt" style="font-size: 4rem; color: #cbd5e1; margin-bottom: 1.5rem;"></i>
                        <h3 style="margin-bottom: 1rem;">Upload Deal Documents</h3>
                        <p style="color: #64748b; margin-bottom: 2rem;">Drag and drop PDF files here or click to browse</p>
                        
                        <form id="upload-form" style="display: none;">
                            <input type="file" id="file-input" accept=".pdf" style="display: none;">
                        </form>
                        
                        <div id="upload-status" style="margin-top: 1rem; display: none;">
                            <div class="spinner" style="margin-bottom: 0.5rem;"><i class="fas fa-spinner fa-spin"></i> Processing...</div>
                            <div class="status-text">Uploading and extracting data...</div>
                        </div>

                        <button id="select-files-btn" class="btn-primary" style="max-width: 200px; margin: 0 auto;">Select Files</button>
                    </div>
                `;
                break;
            case 'active-deals':
                html = `
                    <div class="card">
                        <div class="section-header">
                            <h3>Your Deals</h3>
                            <button class="btn-secondary"><i class="fas fa-plus"></i> New Deal</button>
                        </div>
                        <table style="width: 100%; border-collapse: collapse;">
                            <thead>
                                <tr style="border-bottom: 1px solid #e2e8f0; text-align: left;">
                                    <th style="padding: 1rem; color: #64748b; font-weight: 500;">Deal Name</th>
                                    <th style="padding: 1rem; color: #64748b; font-weight: 500;">Status</th>
                                    <th style="padding: 1rem; color: #64748b; font-weight: 500;">Date</th>
                                    <th style="padding: 1rem; color: #64748b; font-weight: 500;">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td colspan="4" style="padding: 3rem; text-align: center; color: #94a3b8;">
                                        No active deals found. Upload a document to start.
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                `;
                break;
            case 'analysis':
                html = `
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

        // Attach event listeners for specific views
        if (viewName === 'analysis' && state.currentDealId) {
            loadAnalysisData(state.currentDealId);
        }

        async function loadAnalysisData(dealId) {
            try {
                const response = await fetch(`http://localhost:8000/api/analysis/${dealId}`);
                const result = await response.json();

                if (result.success && result.data && Object.keys(result.data).length > 0) {
                    renderAnalysisDashboard(result.data);
                } else {
                    document.getElementById('analysis-content').innerHTML = `
                        <div class="card">
                            <div class="empty-state" style="padding: 4rem; text-align: center;">
                                <i class="fas fa-exclamation-circle" style="font-size: 3rem; color: #ef4444; margin-bottom: 1rem;"></i>
                                <p>Analysis data not found or still processing.</p>
                                <button class="btn-secondary" onclick="renderView('analysis')" style="margin-top: 1rem;">Retry</button>
                            </div>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error fetching analysis:', error);
                document.getElementById('analysis-content').innerHTML = `
                     <div class="card">
                        <p style="color: #ef4444;">Error loading analysis: ${error.message}</p>
                    </div>
                `;
            }
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
                            
                            <div style="margin-bottom: 1rem;">
                                <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem;">EBITDA</h4>
                                <table style="width: 100%; font-size: 0.9rem;">
                                    <tbody>
                                        ${(data.profitMetrics.ebitda || []).map(e => `
                                            <tr>
                                                <td style="padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">${e.period}</td>
                                                <td style="padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9; font-weight: 600;">${e.value} ${e.unit || ''}</td>
                                            </tr>
                                        `).join('')}
                                        ${(!data.profitMetrics.ebitda || data.profitMetrics.ebitda.length === 0) ? '<tr><td style="color: #94a3b8;">No EBITDA data available</td></tr>' : ''}
                                    </tbody>
                                </table>
                            </div>

                            <div>
                                <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem;">Gross Profit</h4>
                                <table style="width: 100%; font-size: 0.9rem;">
                                    <tbody>
                                        ${(data.profitMetrics.grossProfit || []).map(g => `
                                            <tr>
                                                <td style="padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">${g.period}</td>
                                                <td style="padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">${g.value} ${g.unit || ''}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
                            </div>

                            <div style="margin-top: 1rem;">
                                <h4 style="font-size: 0.9rem; margin-bottom: 0.5rem;">Net Income</h4>
                                <table style="width: 100%; font-size: 0.9rem;">
                                    <tbody>
                                        ${(data.profitMetrics.netIncome || []).map(n => `
                                            <tr>
                                                <td style="padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">${n.period}</td>
                                                <td style="padding: 0.5rem 0; border-bottom: 1px solid #f1f5f9;">${n.value} ${n.unit || ''}</td>
                                            </tr>
                                        `).join('')}
                                    </tbody>
                                </table>
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

        if (viewName === 'upload') {
            const selectFilesBtn = document.getElementById('select-files-btn');
            const fileInput = document.getElementById('file-input');
            const uploadStatus = document.getElementById('upload-status');
            const statusText = uploadStatus.querySelector('.status-text');

            selectFilesBtn.addEventListener('click', () => {
                fileInput.click();
            });

            fileInput.addEventListener('change', async (e) => {
                if (e.target.files.length > 0) {
                    const file = e.target.files[0];
                    await uploadFile(file);
                }
            });

            async function uploadFile(file) {
                // Show loading state
                selectFilesBtn.disabled = true;
                selectFilesBtn.style.opacity = '0.5';
                uploadStatus.style.display = 'block';
                statusText.textContent = `Uploading ${file.name}...`;

                const formData = new FormData();
                formData.append('document', file);
                // Generate a temporary deal ID if none exists
                const dealId = 'deal_' + Date.now();
                formData.append('dealId', dealId);

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
                        state.currentDealId = result.dealId || dealId;
                        
                        setTimeout(() => {
                            alert('Document uploaded and processed successfully! Redirecting to analysis...');
                            // Update sidebar active state manually since renderView doesn't do it
                            document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
                            document.querySelector('[data-view="analysis"]').classList.add('active');
                            renderView('analysis'); 
                        }, 1000);
                    } else {
                        throw new Error(result.message || 'Unknown error occurred');
                    }

                } catch (error) {
                    console.error('Error:', error);
                    statusText.textContent = `Error: ${error.message}`;
                    statusText.style.color = '#ef4444';
                } finally {
                    selectFilesBtn.disabled = false;
                    selectFilesBtn.style.opacity = '1';
                }
            }
        }
    }
});
