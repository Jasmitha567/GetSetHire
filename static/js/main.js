// Utility Functions
function showLoading(element) {
    const originalHtml = element.innerHTML;
    element.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    element.disabled = true;
    return originalHtml;
}

function hideLoading(element, originalHtml) {
    element.innerHTML = originalHtml;
    element.disabled = false;
}

function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `alert alert-${type} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    toast.style.zIndex = '9999';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// Skill Gap Visualization
function createSkillGapChart(matchedCount, missingCount) {
    const ctx = document.getElementById('skillGapChart');
    if (!ctx) return;
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Matched Skills', 'Missing Skills'],
            datasets: [{
                data: [matchedCount, missingCount],
                backgroundColor: ['#10b981', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            }
        }
    });
}

// Readiness Score Visualization
function updateReadinessScore(score) {
    const circle = document.querySelector('.progress-ring-circle');
    if (!circle) return;
    
    const radius = circle.r.baseVal.value;
    const circumference = 2 * Math.PI * radius;
    
    circle.style.strokeDasharray = `${circumference} ${circumference}`;
    circle.style.strokeDashoffset = circumference - (score / 100) * circumference;
    
    const scoreElement = document.getElementById('readinessScore');
    if (scoreElement) {
        scoreElement.textContent = score;
    }
}

// Roadmap Timeline Builder
function buildRoadmapTimeline(roadmapData) {
    const timeline = document.getElementById('roadmapTimeline');
    if (!timeline) return;
    
    timeline.innerHTML = '';
    
    roadmapData.weekly_plan.forEach(week => {
        const timelineItem = document.createElement('div');
        timelineItem.className = 'timeline-item';
        timelineItem.innerHTML = `
            <div class="timeline-icon"></div>
            <div class="timeline-content">
                <h5>Week ${week.week}</h5>
                <div class="mb-3">
                    <strong>Skills to focus:</strong>
                    ${week.skills.map(s => `<span class="skill-badge">${s.skill}</span>`).join('')}
                </div>
                <ul class="mb-0">
                    ${week.tasks.map(task => `<li><i class="fas fa-check-circle text-success me-2"></i>${task}</li>`).join('')}
                </ul>
                <div class="mt-2">
                    <small class="text-muted">
                        <i class="fas fa-flag-checkered me-1"></i>
                        ${week.milestones.join(', ')}
                    </small>
                </div>
            </div>
        `;
        timeline.appendChild(timelineItem);
    });
}

// Questionnaire Handler
async function submitQuestionnaire() {
    const form = document.getElementById('questionnaireForm');
    if (!form) return;
    
    const formData = new FormData(form);
    const answers = {};
    formData.forEach((value, key) => {
        answers[key] = value;
    });
    
    const submitBtn = document.querySelector('#submitQuestionnaire');
    const originalHtml = showLoading(submitBtn);
    
    try {
        const response = await fetch('/analyze-questionnaire', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(answers)
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Analysis complete! Redirecting...');
            setTimeout(() => {
                window.location.href = '/results';
            }, 1500);
        } else {
            showToast(data.error || 'Something went wrong', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error analyzing responses', 'danger');
    } finally {
        hideLoading(submitBtn, originalHtml);
    }
}

// Role Selection Handler
async function analyzeWithRole() {
    const role = document.getElementById('jobRole')?.value;
    const company = document.querySelector('.company-badge.active')?.dataset.company;
    const otherCompany = document.getElementById('otherCompany')?.value;
    const prepTime = document.getElementById('prepTime')?.value;
    
    if (!role) {
        showToast('Please select a job role', 'warning');
        return;
    }
    
    let targetCompany = company;
    if (company === 'Other' && otherCompany) {
        targetCompany = otherCompany;
    } else if (!company) {
        showToast('Please select a company', 'warning');
        return;
    }
    
    const analyzeBtn = event.target;
    const originalHtml = showLoading(analyzeBtn);
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                role: role,
                company: targetCompany,
                time: prepTime || 90
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            sessionStorage.setItem('analysisResults', JSON.stringify(data));
            sessionStorage.setItem('targetRole', role);
            sessionStorage.setItem('targetCompany', targetCompany);
            sessionStorage.setItem('prepTime', prepTime || 90);
            window.location.href = '/results';
        } else {
            showToast(data.error || 'Error analyzing skills', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Network error. Please try again.', 'danger');
    } finally {
        hideLoading(analyzeBtn, originalHtml);
    }
}

// File Upload Handler
async function uploadResume() {
    const fileInput = document.getElementById('resumeFile');
    const file = fileInput?.files[0];
    
    if (!file) {
        showToast('Please select a file', 'warning');
        return;
    }
    
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
        showToast('Please upload PDF, DOCX, or TXT file', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('resume', file);
    
    const uploadBtn = document.querySelector('#uploadBtn');
    const originalHtml = showLoading(uploadBtn);
    
    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Resume uploaded and analyzed successfully!');
            setTimeout(() => {
                window.location.href = '/choose-path';
            }, 1500);
        } else {
            showToast(data.error || 'Upload failed', 'danger');
        }
    } catch (error) {
        console.error('Error:', error);
        showToast('Error uploading file', 'danger');
    } finally {
        hideLoading(uploadBtn, originalHtml);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Add company badge click handlers
    document.querySelectorAll('.company-badge').forEach(badge => {
        badge.addEventListener('click', function() {
            document.querySelectorAll('.company-badge').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            const otherCompany = document.getElementById('otherCompany');
            if (this.dataset.company === 'Other' && otherCompany) {
                otherCompany.style.display = 'block';
            } else if (otherCompany) {
                otherCompany.style.display = 'none';
            }
        });
    });
    
    // Load analysis results if on results page
    if (window.location.pathname === '/results') {
        const results = sessionStorage.getItem('analysisResults');
        if (results) {
            const data = JSON.parse(results);
            displayResults(data);
        }
    }
});

function displayResults(data) {
    // Update readiness score
    const readinessElement = document.getElementById('readinessScore');
    if (readinessElement) {
        readinessElement.textContent = data.readiness_score;
        updateReadinessScore(data.readiness_score);
    }
    
    // Display lacking skills
    const lackingSkillsContainer = document.getElementById('lackingSkills');
    if (lackingSkillsContainer && data.lacking_skills) {
        lackingSkillsContainer.innerHTML = data.lacking_skills
            .map(skill => `<span class="skill-badge missing">${skill}</span>`)
            .join('');
    }
    
    // Display roadmap preview
    const roadmapPreview = document.getElementById('roadmapPreview');
    if (roadmapPreview && data.roadmap) {
        roadmapPreview.innerHTML = `
            <div class="mb-3">
                <strong>Total Weeks:</strong> ${data.roadmap.total_weeks}<br>
                <strong>Recommended Hours/Week:</strong> ${data.roadmap.recommended_hours_per_week}
            </div>
            <button class="btn btn-gradient" onclick="window.location.href='/roadmap'">
                View Full Roadmap <i class="fas fa-arrow-right ms-2"></i>
            </button>
        `;
    }
}
