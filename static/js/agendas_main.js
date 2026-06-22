console.log("Agendas Main.js Loaded - Version 1.2 (Fix Date Edit)");
const token = localStorage.getItem('token');
if (!token) window.location.href = '/static/login.html';

// Load Patologias
fetch('/common/patologias', { headers: { 'Authorization': `Bearer ${token}` } })
    .then(r => r.json())
    .then(data => {
        const dl = document.getElementById('cancer-types-list');
        if (dl) {
            dl.innerHTML = '';
            data.forEach(item => {
                const op = document.createElement('option');
                op.value = item;
                dl.appendChild(op);
            });
        }
    })
    .catch(e => console.error("Could not load pathologies", e));


let currentAgendaId = null;
let currentAgendaType = null;
let currentTurnoId = null;

// Variables for confirmation modal
let pendingAction = null;
let pendingId = null;
let pendingStatus = null;

// Set default date to today
const dateFilter = document.getElementById('dateFilter');
if (dateFilter) dateFilter.valueAsDate = new Date();

// Global user variable
window.currentUser = null;

// 🟢 FIX: Return user for proper async handling
async function loadUser() {
    if (!token) return null;
    try {
        const res = await fetch('/users/me', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!res.ok) {
            throw new Error(`Error ${res.status}`);
        }

        const user = await res.json();
        window.currentUser = user; // Store globally

        const userNameDisplay = document.getElementById('user-name-display');
        // Robust Display
        const role = user.role ? user.role.toUpperCase() : 'USER';
        if (userNameDisplay) userNameDisplay.textContent = `${user.username} (${role})`;

        // Robust Check for Admin Links
        if (role === 'ADMIN') {
            const al = document.getElementById('admin-links');
            if (al) al.style.display = 'block';
        }

        return user;

    } catch (e) {
        console.error("Auth Error:", e);
        const userNameDisplay = document.getElementById('user-name-display');
        if (userNameDisplay) {
            userNameDisplay.textContent = 'Error al cargar';
            userNameDisplay.style.color = 'red';
            userNameDisplay.style.fontSize = '0.8rem';
        }
        return null;
    }
}

async function loadAgendas() {
    try {
        const response = await fetch(`/agendas/?_=${new Date().getTime()}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.status === 401) {
            logout();
            return;
        }

        const agendas = await response.json();
        renderAgendaList(agendas);

        // ✨ Auto-select logic if only 1 agenda exists (Fix for Doctors)
        if (agendas.length === 1) {
            const firstAgenda = agendas[0];
            const item = document.querySelector(`.agenda-item[data-id="${firstAgenda.id}"]`);
            if (item) selectAgendaFromClick(item);
        }

    } catch (error) {
        console.error('Error loading agendas:', error);
        const agendaList = document.getElementById('agendaList');
        if (agendaList) agendaList.innerHTML = '<div style="text-align: center; padding: 1rem; color: #f56565;">Error al cargar agendas</div>';
    }
}

// 🚀 SEQUENTIAL INITIALIZATION
// This guarantees that User Permissions are loaded BEFORE Agendas/Slots are ever requested.
async function init() {
    console.log("🚀 Starting App Initialization...");
    await loadUser();
    console.log("✅ User Loaded. Current User:", window.currentUser);
    await loadAgendas();
    console.log("✅ Agendas Loaded.");
}

// Start the sequence
init();


function renderAgendaList(agendas) {
    const container = document.getElementById('agendaList');
    if (!container) return;
    container.innerHTML = agendas.map(agenda => `
        <div class="agenda-item" 
             data-id="${agenda.id}" 
             data-name="${agenda.nombre.replace(/"/g, '&quot;')}" 
             data-type="${agenda.tipo}"
             onclick="selectAgendaFromClick(this)">
            <div class="dot"></div>
            <div>
                <div style="font-weight: 500;">${agenda.nombre}</div>
                <div style="font-size: 0.75rem; color: #718096; text-transform: uppercase;">${agenda.tipo}</div>
            </div>
        </div>
    `).join('');
}

window.selectAgendaFromClick = function (element) {
    const id = element.dataset.id;
    const name = element.dataset.name;
    const type = element.dataset.type;

    document.querySelectorAll('.agenda-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');

    document.getElementById('currentAgendaTitle').textContent = name;
    const filtersBar = document.getElementById('filtersBar');
    if (filtersBar) filtersBar.style.display = 'flex';

    currentAgendaId = id;
    currentAgendaType = type;

    // loadPracticas(type); // Eliminado
    loadSlots();
}

window.filterSlots = function () {
    const term = document.getElementById('pacienteFilter').value.toLowerCase();

    if (!currentSlots) return;

    // If empty, show all (re-render original fetched slots)
    if (!term) {
        renderSlots(currentSlots);
        return;
    }

    const filtered = currentSlots.filter(s => {
        if (!s.turno) return false; // Hide empty slots when searching

        const p = s.turno.paciente;
        if (!p) return false;

        const fullName = `${p.nombre} ${p.apellido}`.toLowerCase();
        const dni = p.dni ? p.dni.toString() : '';

        return fullName.includes(term) || dni.includes(term);
    });

    renderSlots(filtered);
}

async function loadSlots() {
    if (!currentAgendaId) return;

    const container = document.getElementById('turnosContainer');
    if (container) container.innerHTML = '<div style="text-align: center; padding: 4rem; color: #718096;">Cargando disponibilidad...</div>';

    const date = document.getElementById('dateFilter').value;

    try {
        let url = `/agendas/${currentAgendaId}/slots?fecha=${date}&_=${new Date().getTime()}`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        const slots = await response.json();
        currentSlots = slots; // Store for access
        renderSlots(slots);
    } catch (error) {
        console.error(error);
        if (container) container.innerHTML = '<p style="color: #f56565; text-align: center; padding: 2rem;">Error al cargar disponibilidad</p>';
    }
}

function renderSlots(slots) {
    const container = document.getElementById('turnosContainer');
    const statsContainer = document.getElementById('agendaStats');

    // 🟢 Statistics Logic
    let occupiedCount = 0;
    let availableCount = 0;

    slots.forEach(s => {
        if (s.turno) occupiedCount++;
        else if (s.disponible) availableCount++;
    });

    // Update UI Stats
    if (statsContainer) {
        if (slots.length > 0 || currentAgendaId) {
            statsContainer.style.display = 'flex';
            statsContainer.innerHTML = `
                <div style="background: #EBF8FF; color: #2B6CB0; padding: 0.25rem 0.75rem; border-radius: 999px; font-weight: 600; border: 1px solid #BEE3F8;">
                    Otorgados: ${occupiedCount}
                </div>
                <div style="background: #F0FFF4; color: #2F855A; padding: 0.25rem 0.75rem; border-radius: 999px; font-weight: 600; border: 1px solid #C6F6D5;">
                    Disponibles: ${availableCount}
                </div>
            `;
        } else {
            statsContainer.style.display = 'none';
        }
    }

    if (!container) return;

    if (slots.length === 0) {
        container.innerHTML = '<div style="text-align: center; padding: 4rem; color: #a0aec0;">No hay horarios disponibles para esta fecha</div>';
        return;
    }

    let html = `
        <table class="turnos-table">
            <thead>
                <tr>
                    <th>Hora</th>
                    <th>Paciente</th>
                    <th>Estado</th>
                    <th>Acciones</th>
                </tr>
            </thead>
            <tbody>
    `;

    const dateFilter = document.getElementById('dateFilter');
    const selectedDate = dateFilter && dateFilter.value ? dateFilter.value : new Date().toISOString().split('T')[0];

    slots.forEach(slot => {
        // 🟢 FIX: Handle Multiple Turnos (Overflow)
        // Backend now returns all turnos in the slot logic if we changed it, 
        // OR we need to adapt if the backend returns a list in 'turno' or if it returns multiple slots with same time?
        // CURRENT BACKEND FIX (routers/agendas.py): It returns multiple objects in 'slots' array with SAME time if overflow exists.
        // So 'slots' array might have:
        // { time: 09:00, turno: T1 }
        // { time: 09:00, turno: T2 }
        // We need to GROUP them by time to render in the same row, or render them as separate rows?
        // Standard Agenda View usually expects 1 row per time slot.
        // Let's Group by Time first.
    });

    // Group slots by time
    const groupedSlots = {};
    slots.forEach(s => {
        if (!groupedSlots[s.hora]) groupedSlots[s.hora] = [];
        groupedSlots[s.hora].push(s);
    });

    Object.keys(groupedSlots).sort().forEach(time => {
        const group = groupedSlots[time];
        const turnosInSlot = group.filter(s => s.turno);
        const availableInSlot = group.filter(s => !s.turno && s.disponible);

        // Calculate Capacity
        let capacity = 1;
        if (currentAgendaType === 'QUIMIOTERAPIA') capacity = 7;

        // --- Render Logic ---

        // Case A: No appointments (Empty Slot)
        if (turnosInSlot.length === 0) {
            html += `<tr>
                <td style="vertical-align: top; padding-top: 12px;">
                    <span style="font-weight: 500; color: #2d3748;">${time}</span>
                </td>
                <td style="vertical-align: top;">`;

            // Available Message
            if (availableInSlot.length > 1) {
                html += `<span style="color: #38A169; font-weight:500;">${availableInSlot.length} Lugares Disponibles</span>`;
            } else {
                html += `<span style="color: #a0aec0;">Disponible</span>`;
            }

            html += `</td>
                <td>-</td>
                <td style="vertical-align: top;">
                    <button class="action-btn btn-confirm" onclick="agendar('${selectedDate}', '${time}')">Agendar</button>
                </td>
            </tr>`;

        } else {
            // Case B: Appointments Exist (Render 1 Row per Patient)
            turnosInSlot.forEach((s, index) => {
                html += `<tr>`;

                // 1. Time Column (Only on first row, with RowSpan)
                if (index === 0) {
                    html += `<td rowspan="${turnosInSlot.length}" style="vertical-align: top; padding-top: 12px; border-right: 1px solid #edf2f7;">`;
                    html += `<span style="font-weight: 500; color: #2d3748;">${time}</span>`;

                    if (turnosInSlot.length > capacity) {
                        html += `<br><span style="background: #FEB2B2; color: #C53030; font-size: 0.65rem; padding: 2px 4px; border-radius: 4px; font-weight: bold; display: inline-block; margin-top: 4px;">SOBRETURNO (${turnosInSlot.length}/${capacity})</span>`;
                    }
                    html += `</td>`;
                }

                // 2. Patient Column
                const turno = s.turno;
                const p = turno.paciente;
                const nombre = p ? `${p.nombre} ${p.apellido}` : 'ID: ' + turno.paciente_id;

                html += `<td style="vertical-align: top; padding: 12px 0; border-bottom: 1px solid #edf2f7; cursor: pointer;" onclick="openTurnoDetails(${turno.id})" title="Ver Detalles del Turno">
                    <div class="clickable-patient-name" style="font-weight: 600; color: #2b6cb0; text-decoration: underline;">${nombre}</div>
                    ${turno.patologia ? `<div style="font-size: 0.8rem; color: #718096; margin-top: 2px;">${turno.patologia}</div>` : ''}
                </td>`;

                // 3. Status Column
                const estado = turno.estado ? turno.estado.toUpperCase() : 'DESCONOCIDO';
                const estadoClass = turno.estado ? turno.estado.toLowerCase() : 'unknown';

                html += `<td style="vertical-align: top; padding-top: 12px;">
                    <span class="status-badge status-${estadoClass}">${estado}</span>
                </td>`;

                // 4. Actions Column
                const isAdmin = window.currentUser && window.currentUser.role && window.currentUser.role.toLowerCase() === 'admin';

                html += `<td style="vertical-align: top; padding-top: 12px;">
                    <div style="display: flex; flex-wrap: wrap; gap: 6px;">`;

                // Edit Btn
                html += `<button class="action-btn" onclick="openEditPatientModal(${turno.paciente_id}, ${turno.id})" title="Editar Datos Paciente" style="background: #e2e8f0;">✏️</button>`;

                if (estado !== 'COMPLETADO') {
                    html += `
                        <button class="action-btn btn-waiting" onclick="requestUpdateStatus(${turno.id}, 'ESPERANDO')" title="Esperando">🕙</button>
                        <button class="action-btn btn-complete" onclick="triggerComplete(${turno.id})" title="Completar">✅</button>
                        <button class="action-btn btn-reschedule" onclick="triggerReschedule(${turno.id})" title="Reprogramar">📅</button>
                    `;

                    const whatsappClass = turno.recordatorio_enviado ? 'btn-whatsapp-sent' : 'btn-whatsapp';
                    const whatsappTitle = turno.recordatorio_enviado ? 'Re-enviar WhatsApp (Ya enviado)' : 'Enviar WhatsApp';
                    html += `<button class="action-btn ${whatsappClass}" onclick="sendWhatsapp(${turno.id}, this)" title="${whatsappTitle}">💬</button>`;

                    // Radiotherapy Tracking
                    html += `<button class="action-btn" onclick="startRadiotherapy(${turno.id}, this)" title="Iniciar Seguimiento Radioterapia" style="background: #FFF5F5; border: 1px solid #FC8181; color: #C53030;">☢️</button>`;

                    // Clinical History / Evolution
                    // Redirección a la página completa de Historial
                    const safeDni = p ? p.dni : '';
                    html += `<button class="action-btn" onclick="window.location.href='/static/historial_turnos.html?dni=${safeDni}'" title="Ver Historial Paciente" style="background: #e2e8f0;">📋</button>`;
                }

                // 🟢 FIX: Botón de Ausente disponible para no-completados, o para admins incluso si está completado.
                if (estado !== 'AUSENTE' && (estado !== 'COMPLETADO' || isAdmin)) {
                    html += `<button class="action-btn btn-absent" onclick="requestUpdateStatus(${turno.id}, 'AUSENTE')" title="Ausente">❌</button>`;
                }

                if (estado !== 'COMPLETADO' || isAdmin) {
                    html += `<button class="action-btn" onclick="deleteTurno(${turno.id}, '${estado}')" title="ELIMINAR TURNO" style="background: #FED7D7; border: 1px solid #F56565; color: #C53030;">🗑️</button>`;
                }

                html += `</div></td>`;
                html += `</tr>`;
            });
        }
    });

    html += `</tbody></table>`;
    container.innerHTML = html;
}

// 🟢 NEW: Delete Turn Function
window.deleteTurno = async function (id, estado) {
    let msg = "⚠️ ¿ESTÁ SEGURO DE QUE DESEA ELIMINAR ESTE TURNO?\n\nEsta acción es irreversible y borrará el turno de la base de datos para siempre.";

    // Strict Warning for Completed
    if (estado === 'COMPLETADO') {
        msg = "🛑 ¡ADVERTENCIA CRÍTICA! 🛑\n\nEste turno ya figura como COMPLETADO.\n\n¿Está seguro de que desea eliminarlo?\nEsta acción podría afectar las estadísticas de atención y el historial del paciente.";
    }

    if (!confirm(msg)) return;

    try {
        const response = await fetch(`/turnos/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.ok) {
            loadSlots();
            alert('Turno eliminado correctamente.');
        } else {
            const err = await response.text();
            alert('Error al eliminar: ' + err);
        }
    } catch (e) {
        console.error(e);
        alert('Error de conexión');
    }
}

// 🟢 NEW: Start Radiotherapy Function
window.startRadiotherapy = async function (id, btn) {
    if (!confirm("¿Iniciar Seguimiento de Radioterapia para este paciente?\n\nEsto creará un registro activo si no existe.")) return;

    const originalText = btn.innerHTML;
    btn.innerHTML = '...';
    btn.disabled = true;

    try {
        const response = await fetch(`/turnos/${id}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ crear_seguimiento: true })
        });

        if (response.ok) {
            alert('Seguimiento Iniciado / Verificado.');
            // Optional: Change icon to indicate success
            btn.style.background = "#C6F6D5";
            btn.style.borderColor = "#68D391";
            btn.style.color = "#22543D";
            btn.innerHTML = "☢️✅";
        } else {
            const err = await response.text();
            alert('Error: ' + err);
        }
    } catch (e) {
        console.error(e);
        alert('Error de conexión');
    } finally {
        if (btn.innerHTML === '...') {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    }
}

window.agendar = function (fechaIso, hora) {
    if (!currentAgendaId) return;
    const dateStr = fechaIso.split('T')[0];

    const params = new URLSearchParams({
        agenda_id: currentAgendaId,
        fecha: dateStr,
        hora: hora
    });
    window.location.href = `/static/nuevo_turno.html?${params.toString()}`;
}

window.openReschedule = function (id) {
    console.log("openReschedule called:", id);
    currentTurnoId = id;
    const modal = document.getElementById('rescheduleModal');
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
    }
}

window.closeModal = function () {
    console.log("closeModal called");
    // Aggressive cleanup
    document.querySelectorAll('.modal').forEach(m => {
        m.classList.remove('active');
        m.style.display = 'none';
    });
    currentTurnoId = null;
}

window.confirmReschedule = async function () {
    if (!currentTurnoId) return;

    const newDate = document.getElementById('newDate').value;
    const newTime = document.getElementById('newTime').value;

    if (!newDate || !newTime) {
        alert('Ingrese fecha y hora');
        return;
    }

    const btn = document.querySelector('#rescheduleModal .btn-confirm');
    const originalText = btn.textContent;
    btn.textContent = 'Guardando...';
    btn.disabled = true;

    // Find current turno data
    let foundTurno = null;
    if (currentSlots) {
        for (let s of currentSlots) {
            if (s.turno && s.turno.id === currentTurnoId) {
                foundTurno = s.turno;
                break;
            }
        }
    }

    // 🟢 VALIDATE SUNDAY
    const d = new Date(newDate + 'T00:00:00');
    if (d.getDay() === 0) { // 0 = Sunday
        alert('No se pueden agendar turnos los días Domingo.');
        btn.textContent = originalText;
        btn.disabled = false;
        return;
    }

    try {
        // BRANCH LOGIC: If AUSENTE -> Create NEW Turno. Else -> PATCH.
        if (foundTurno && foundTurno.estado === 'AUSENTE') {
            // Create Clone
            const payload = {
                paciente_id: foundTurno.paciente_id,
                agenda_id: foundTurno.agenda_id || parseInt(currentAgendaId), // 👈 FIX: Fallback to global
                fecha: newDate,
                hora: newTime,
                duracion: foundTurno.duracion || 20,
                estado: "PENDIENTE",
                medico_derivante_id: foundTurno.medico_derivante_id,
                patologia: foundTurno.patologia,
                crear_seguimiento: false, // Don't duplicate logic, but dates will update
                practicas_ids: foundTurno.practicas ? foundTurno.practicas.map(p => p.id) : []
            };

            const response = await fetch('/turnos/', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            if (response.ok) {
                alert('Nuevo turno creado (El anterior permanece como Ausente)');
                closeModal();
                loadSlots();
            } else {
                const err = await response.text();
                alert('Error al crear nuevo turno: ' + err);
            }

        } else {
            // Standard Reschedule (PATCH)
            const response = await fetch(`/turnos/${currentTurnoId}`, {
                method: 'PATCH',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    fecha: newDate,
                    hora: newTime
                })
            });

            if (response.ok) {
                alert('Turno reprogramado exitosamente');
                closeModal();
                loadSlots();
            } else {
                const err = await response.text();
                alert('Error al reprogramar: ' + err);
            }
        }

    } catch (error) {
        console.error(error);
        alert('Error de conexión');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

window.sendWhatsapp = async function (turnoId, btnInfo) {
    try {
        // 1. Obtener enlace
        const response = await fetch(`/whatsapp/link/${turnoId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();

            // 2. Abrir WhatsApp
            window.open(data.link, '_blank');

            // 3. Marcar como enviado en backend
            await markAsSent(turnoId, btnInfo);

        } else {
            const err = await response.json();
            alert('Error: ' + err.detail);
        }
    } catch (error) {
        console.error(error);
        alert('Error al generar enlace de WhatsApp');
    }
}

async function markAsSent(turnoId, btnElement) {
    try {
        await fetch(`/whatsapp/mark-sent/${turnoId}`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        // Actualizar UI
        if (btnElement) {
            btnElement.classList.remove('btn-whatsapp');
            btnElement.classList.add('btn-whatsapp-sent');
            btnElement.title = "Re-enviar WhatsApp (Ya enviado)";
            btnElement.innerHTML = "✅ Mensaje"; // O mantener icono pero cambiar color
        }

        // Opcional: recargar slots para estar seguros, o actualizar variable local
        // loadSlots(); 
    } catch (e) {
        console.error("Error marcando como enviado", e);
    }
}

// --- Logic for Status Update with Custom Modal ---

window.requestUpdateStatus = function (id, status) {
    console.log("requestUpdateStatus called:", id, status);
    pendingId = id;
    pendingStatus = status;
    pendingAction = 'UPDATE_STATUS';

    const msg = status === 'COMPLETADO'
        ? '¿Desea marcar este turno como COMPLETADO?'
        : (status === 'ESPERANDO' ? '¿Desea marcar este turno como ESPERANDO?' : '¿Desea marcar este turno como AUSENTE?');

    const modal = document.getElementById('confirmationModal');
    if (modal) {
        document.getElementById('confirmationMessage').textContent = msg;
        modal.classList.add('active');
        modal.style.display = 'flex'; // Force display
    } else {
        console.error("Confirmation modal not found!");
    }
}

window.closeConfirmation = function () {
    console.log("closeConfirmation called");
    // Aggressive cleanup
    document.querySelectorAll('.modal').forEach(m => {
        m.classList.remove('active');
        m.style.display = 'none';
    });
    pendingId = null;
    pendingStatus = null;
    pendingAction = null;
}

window.executeAction = async function () {
    if (!pendingAction) return;

    const btn = document.getElementById('btnConfirmAction');
    const originalText = btn.textContent;
    btn.textContent = '...';
    btn.disabled = true;

    try {
        if (pendingAction === 'UPDATE_STATUS') {
            await performUpdateStatus(pendingId, pendingStatus);
        }
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
        closeConfirmation();
    }
}

window.performUpdateStatus = async function (id, status) {
    if (!token) {
        alert('Sesión expirada');
        logout();
        return;
    }

    try {
        const response = await fetch(`/turnos/${id}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ estado: status })
        });

        if (response.status === 401) {
            logout();
            return;
        }

        if (response.ok) {
            loadSlots();
        } else {
            const txt = await response.text();
            alert('Error al actualizar estado: ' + txt);
        }
    } catch (error) {
        console.error(error);
        alert('Error de conexión');
    }
}

window.logout = function () {
    localStorage.removeItem('token');
    window.location.href = '/static/login.html';
}

// --- Historia Clinica Logic ---
let currentHistoriaPacienteId = null;
let currentNoteId = null;
let eventsMap = {};

window.openNoteModal = function (note = null, readOnly = false, patientData = null) {
    const modal = document.getElementById('noteModal');
    if (modal) modal.classList.add('active');

    // Setup Buttons & Title
    if (modal) {
        const actionsDiv = modal.querySelector('.modal-actions');
        const title = modal.querySelector('.modal-title');

        // Reset Form
        const form = document.getElementById('noteForm');
        if (!note && form) form.reset();

        // Handle Patient Data for new notes
        if (patientData) {
            currentHistoriaPacienteId = patientData.id;
        }

        if (readOnly) {
            if (title) title.textContent = "Detalle de Evolución";
            if (actionsDiv) actionsDiv.style.display = 'none';
            if (form) form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = true);
        } else {
            if (title) title.textContent = "Nueva Evolución";
            if (actionsDiv) actionsDiv.style.display = 'flex';
            if (form) form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = false);
        }

        if (note) {
            const sc = note.structured_content || {};
            document.getElementById('note-ecog').value = sc.ecog || '';
            document.getElementById('note-tnm').value = sc.tnm || '';
            document.getElementById('note-estadio').value = sc.estadio || '';
            document.getElementById('note-toxicidad').value = sc.toxicidad || '';
            document.getElementById('note-radio-check').checked = sc.requiere_radioterapia || false;

            document.getElementById('note-motivo').value = sc.motivo || '';
            document.getElementById('note-antecedentes').value = sc.antecedentes || '';
            document.getElementById('note-examen').value = sc.examen || '';
            document.getElementById('note-diagnostico').value = sc.dx_dif || '';
            document.getElementById('note-plan').value = sc.plan || '';
            document.getElementById('note-tratamiento').value = sc.tratamiento || '';
        }
    }
}

window.closeNoteModal = function () {
    const modal = document.getElementById('noteModal');
    if (modal) modal.classList.remove('active');
    const form = document.getElementById('noteForm');
    if (form) {
        form.reset();
        // Re-enable 
        form.querySelectorAll('input, textarea, select').forEach(el => el.disabled = false);
    }
}

window.viewHistoryFromModal = function () {
    if (currentHistoriaPacienteId) {
        // En este caso, el modal NoteModal está dentro de Agendas.html
        // Si queremos ir al historial completo desde el modal de evolución rápida:
        const dni = window.currentHistoriaPacienteDni || '';
        window.location.href = `/static/historial_turnos.html?dni=${dni}`;
    }
}

window.submitNote = async function (estado) {
    if (!currentHistoriaPacienteId) { alert("Error: Paciente no identificado"); return; }
    if (estado === 'FIRMADO' && !confirm("¿Firmar nota? No se podrá editar.")) return;

    const structuredData = {
        ecog: document.getElementById('note-ecog').value,
        tnm: document.getElementById('note-tnm').value,
        estadio: document.getElementById('note-estadio').value,
        toxicidad: document.getElementById('note-toxicidad').value,
        requiere_radioterapia: document.getElementById('note-radio-check').checked,

        motivo: document.getElementById('note-motivo').value,
        antecedentes: document.getElementById('note-antecedentes').value,
        examen: document.getElementById('note-examen').value,
        dx_dif: document.getElementById('note-diagnostico').value,
        plan: document.getElementById('note-plan').value,
        tratamiento: document.getElementById('note-tratamiento').value
    };

    // Basic Validation
    if (!structuredData.motivo && !structuredData.examen) {
        alert("Ingrese al menos Motivo o Examen Físico");
        return;
    }

    const btn = document.querySelector(`.btn-confirm[onclick*="${estado}"]`);
    const originalText = btn ? btn.textContent : 'Guardar';
    if (btn) { btn.textContent = 'Guardando...'; btn.disabled = true; }

    try {
        const res = await fetch('/historia-clinica/', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paciente_id: currentHistoriaPacienteId,
                estado: estado,
                servicio: currentAgendaType || 'CONSULTORIO',
                structured_content: structuredData
            })
        });

        if (res.ok) {
            alert("Nota guardada correctamente");
            closeNoteModal();
        } else {
            const err = await res.json();
            alert("Error: " + (err.detail || "Error al guardar"));
        }
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    } finally {
        if (btn) { btn.textContent = originalText; btn.disabled = false; }
    }
}

window.openHistoria = async function (pacienteId, dni, nombre) {
    currentHistoriaPacienteId = pacienteId;
    // Update Badge
    const badge = document.getElementById('historiaPacienteBadge');
    if (badge) badge.innerHTML = `<strong>${nombre}</strong> <span style="opacity: 0.7;">|</span> DNI: ${dni}`;

    const modal = document.getElementById('historiaModal');
    if (modal) modal.classList.add('active');
    await loadHistoriaTimeline(pacienteId);
}

window.closeHistoria = function () {
    const modal = document.getElementById('historiaModal');
    if (modal) modal.classList.remove('active');
    currentHistoriaPacienteId = null;
}

window.loadHistoriaTimeline = async function (pacienteId) {
    const container = document.getElementById('historiaTimeline');
    if (container) container.innerHTML = '<div style="text-align: center; padding: 3rem; color: #a0aec0;">Cargando historia...</div>';

    try {
        const res = await fetch(`/historia-clinica/paciente/${pacienteId}/timeline`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('Error al cargar');

        const data = await res.json();
        renderTimeline(data.timeline);
    } catch (e) {
        console.error(e);
        if (container) container.innerHTML = '<div style="color: #e53e3e; text-align: center; padding: 2rem;">Error al cargar historia clínica.</div>';
    }
}

function renderTimeline(events) {
    const container = document.getElementById('historiaTimeline');
    if (!container) return;
    eventsMap = {}; // Reset map

    if (!events || events.length === 0) {
        container.innerHTML = `
            <div style="text-align: center; padding: 4rem; color: #a0aec0;">
                <div style="font-size: 3rem; margin-bottom: 1rem;">📭</div>
                <p>No hay registros en la historia clínica.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = events.map(ev => {
        if (ev.id_referencia) eventsMap[ev.id_referencia] = ev; // Index

        const isNota = ev.tipo === 'NOTA';
        let icon = '📝';
        let typeClass = 'type-nota';
        let title = isNota ? 'Nota de Evolución' : ev.descripcion;

        // Determine Icon and Color based on content
        if (!isNota) {
            const descUpper = ev.descripcion.toUpperCase();
            if (descUpper.includes('QUIMIO')) { icon = '💧'; typeClass = 'type-quimio'; }
            else if (descUpper.includes('TOMO') || descUpper.includes('RADIO')) { icon = '☢️'; typeClass = 'type-tomo'; }
            else { icon = '🏥'; typeClass = 'type-consult'; }
        } else {
            // Check service for manual notes
            const srv = (ev.servicio || '').toUpperCase();
            if (srv === 'QUIMIOTERAPIA') { typeClass = 'type-quimio'; }
            if (srv === 'TOMOGRAFIA') { typeClass = 'type-tomo'; }
        }

        const dateObj = new Date(ev.fecha);
        const dateStr = dateObj.toLocaleDateString('es-AR', { day: 'numeric', month: 'short', year: 'numeric' });
        const timeStr = dateObj.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });

        // Add View Detail Button for Notes
        let actions = '';
        if (isNota) {
            actions = `<button onclick="openNoteModal(eventsMap[${ev.id_referencia}], true)" 
             style="float:right;background:none;border:none;color:#2b6cb0;cursor:pointer;font-size:0.85rem">👁️ Ver Detalle</button>`;
        }

        return `
            <div class="timeline-card">
                <div class="timeline-icon ${typeClass}">${icon}</div>
                
                <div class="timeline-header-row">
                    <div class="timeline-title">${title} ${actions}</div>
                    <div class="timeline-date">${dateStr} • ${timeStr}</div>
                </div>

                <div class="timeline-body">${ev.detalle}</div>
                
                ${ev.servicio && ev.servicio !== 'GENERAL' ?
                `<span class="timeline-badge" style="background: #edf2f7; color: #718096; margin-top: 0.75rem;">${ev.servicio}</span>` : ''}
                
                ${ev.estado ?
                `<span class="timeline-badge" style="background: ${getStatusColor(ev.estado)}; color: white; margin-left: 0.5rem;">${ev.estado}</span>` : ''}
            </div>
        `;
    }).join('');
}

function getStatusColor(status) {
    const s = status.toUpperCase();
    if (s === 'COMPLETADO' || s === 'ASISTIÓ') return '#48bb78'; // Green
    if (s === 'ESPERANDO') return '#d97706'; // Amber
    if (s === 'AUSENTE' || s === 'CANCELADO') return '#f56565'; // Red
    if (s === 'PENDIENTE') return '#4299e1'; // Blue
    return '#a0aec0'; // Gray
}

window.saveHistoria = async function () {
    if (!currentHistoriaPacienteId) return;
    const texto = document.getElementById('nuevaNotaTexto').value;
    const servicio = document.getElementById('nuevaNotaServicio').value;

    if (!texto) return alert("Escriba una nota");

    const btn = document.querySelector('#historiaModal .btn-primary');
    const originalText = btn.textContent;
    btn.textContent = 'Guardando...';
    btn.disabled = true;

    try {
        const res = await fetch('/historia-clinica/', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({
                paciente_id: currentHistoriaPacienteId,
                texto: texto,
                servicio: servicio
            })
        });

        if (res.ok) {
            document.getElementById('nuevaNotaTexto').value = '';
            await loadHistoriaTimeline(currentHistoriaPacienteId);
        } else {
            alert('Error al guardar nota');
        }
    } catch (e) {
        console.error(e);
        alert('Error de conexión');
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

window.printHistoria = function () {
    document.body.classList.add('printing-historia');
    window.print();
    document.body.classList.remove('printing-historia');
}

// --- EDIT PATIENT LOGIC ---
let currentTurnoIdEdit = null; // New global to store the context

window.openEditPatientModal = async function (patientId, turnoId = null) {
    currentPatientIdEdit = patientId;
    currentTurnoIdEdit = turnoId;

    if (!currentPatientIdEdit) { alert("No hay paciente seleccionado"); return; }

    // Load Lists if empty
    if (document.getElementById('os-list').children.length === 0) {
        try {
            const [osData, medData] = await Promise.all([
                fetch('/obras-sociales/', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json()),
                fetch('/common/medicos-derivantes', { headers: { 'Authorization': `Bearer ${token}` } }).then(r => r.json())
            ]);

            const osList = document.getElementById('os-list');
            osData.forEach(item => {
                const op = document.createElement('option');
                op.value = item.nombre;
                osList.appendChild(op);
            });

            const medList = document.getElementById('medicos-list');
            medData.forEach(item => {
                const op = document.createElement('option');
                op.value = item.nombre;
                medList.appendChild(op);
            });
        } catch (e) {
            console.error("Error loading lists", e);
        }
    }

    // Load Patient Data
    try {
        const res = await fetch(`/pacientes/${currentPatientIdEdit}`, { headers: { 'Authorization': `Bearer ${token}` } });
        if (!res.ok) throw new Error("Error loading patient");
        const p = await res.json();

        document.getElementById('edit-nombre').value = p.nombre;
        document.getElementById('edit-apellido').value = p.apellido;
        const dniInput = document.getElementById('edit-dni');
        dniInput.value = p.dni;
        // 🟢 FIX: Explicitly unlock DNI
        dniInput.readOnly = false;
        dniInput.disabled = false;
        dniInput.style.cursor = 'text';
        dniInput.style.backgroundColor = 'white';

        const fechaInput = document.getElementById('edit-fecha-nacimiento');
        fechaInput.value = p.fecha_nacimiento || '';
        fechaInput.readOnly = false;
        fechaInput.disabled = false;

        document.getElementById('edit-telefono').value = p.telefono || '';
        document.getElementById('edit-obra-social').value = p.obra_social ? p.obra_social.nombre : '';
        document.getElementById('edit-medico').value = p.medico_derivante ? p.medico_derivante.nombre : '';

        // Load Patologia (fallback to patient's central pathology)
        document.getElementById('edit-patologia').value = p.patologia || '';

        // If Context Turno exists, override/populate fields from Turno
        if (currentTurnoIdEdit) {
            // Try to find turno in global cache first
            let foundTurno = null;
            if (currentSlots) {
                for (let s of currentSlots) {
                    if (s.turno && s.turno.id === currentTurnoIdEdit) {
                        foundTurno = s.turno;
                        break;
                    }
                }
            }

            if (foundTurno && foundTurno.patologia) {
                document.getElementById('edit-patologia').value = foundTurno.patologia;
            }
        }

        const editPatientModal = document.getElementById('editPatientModal');
        if (editPatientModal) editPatientModal.style.display = 'flex';
    } catch (e) {
        console.error(e);
        alert("Error cargando datos del paciente");
    }
}

function closeEditPatientModal() {
    const editPatientModal = document.getElementById('editPatientModal');
    if (editPatientModal) editPatientModal.style.display = 'none';
}

async function submitEditPatient() {
    const nombre = document.getElementById('edit-nombre').value;
    const apellido = document.getElementById('edit-apellido').value;
    const fecha_nacimiento = document.getElementById('edit-fecha-nacimiento').value || null;
    const telefono = document.getElementById('edit-telefono').value;
    const dni = document.getElementById('edit-dni').value;
    const obra_social_nombre = document.getElementById('edit-obra-social').value;
    const medico_derivante_nombre = document.getElementById('edit-medico').value;
    const patologia = document.getElementById('edit-patologia').value;

    const payloadPaciente = {
        nombre, apellido, fecha_nacimiento, telefono, dni,
        obra_social_nombre, medico_derivante_nombre, patologia
    };

    const btn = document.querySelector('#editPatientModal .btn-primary');
    const originalText = btn.textContent;
    btn.textContent = 'Guardando...';
    btn.disabled = true;

    try {
        // 1. Update Patient
        const res = await fetch(`/pacientes/${currentPatientIdEdit}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify(payloadPaciente)
        });

        if (!res.ok) {
            const err = await res.json();
            console.error("Error response:", err);
            let msg = "Error al actualizar Paciente";
            if (err.detail) {
                if (typeof err.detail === 'string') {
                    msg = "Error: " + err.detail;
                } else if (Array.isArray(err.detail)) {
                    msg = "Error de Validación: " + err.detail.map(e => e.msg).join(", ");
                } else {
                    msg = "Error: " + JSON.stringify(err.detail);
                }
            }
            throw new Error(msg);
        }

        // 2. Update Turno (if context exists)
        if (currentTurnoIdEdit) {
            const resTurno = await fetch(`/turnos/${currentTurnoIdEdit}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                body: JSON.stringify({ patologia: patologia })
            });

            if (!resTurno.ok) {
                console.warn("Patient updated but error updating Turno pathology");
            }
        }

        alert("Datos actualizados correctamente");
        closeEditPatientModal();
        loadSlots(); // Refresh UI

    } catch (e) {
        console.error(e);
        alert(e.message || "Error desconocido");
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}

loadAgendas();

// PASTE IMAGE LOGIC
function enableImagePaste() {
    // Use Event Delegation for better reliability
    document.addEventListener('paste', async (e) => {
        const target = e.target;
        if (target.tagName === 'TEXTAREA') {
            console.log("Paste detected on textarea");
            const items = (e.clipboardData || e.originalEvent.clipboardData).items;

            for (let index in items) {
                const item = items[index];
                if (item.kind === 'file') {
                    const blob = item.getAsFile();
                    console.log("File detected:", blob.type);
                    if (blob.type.startsWith('image/')) {
                        e.preventDefault();
                        await uploadAndInsertImage(blob, target);
                        return; // Stop after first image found
                    }
                }
            }
        }
    });
}

async function uploadAndInsertImage(blob, textarea) {
    const formData = new FormData();
    formData.append('file', blob);

    // Show uploading state
    const originalPlaceholder = textarea.placeholder;
    textarea.placeholder = "Subiendo imagen...";

    // Insert temporary text
    const cursorPos = textarea.selectionStart;
    const textBefore = textarea.value.substring(0, cursorPos);
    const textAfter = textarea.value.substring(cursorPos);
    textarea.value = textBefore + " [...Subiendo Imagen...] " + textAfter;

    try {
        const res = await fetch('/uploads/image', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData
        });

        if (res.ok) {
            const data = await res.json();
            const link = `\n(Ver Imagen: [${data.filename}](${data.url}))\n`;

            // Replace temp text with actual link
            textarea.value = textarea.value.replace(" [...Subiendo Imagen...] ", link);
        } else {
            alert("Error al subir imagen");
            textarea.value = textarea.value.replace(" [...Subiendo Imagen...] ", "");
        }
    } catch (err) {
        console.error(err);
        alert("Error de conexión al subir imagen");
        textarea.value = textarea.value.replace(" [...Subiendo Imagen...] ", "");
    } finally {
        textarea.placeholder = originalPlaceholder;
    }
}

// Wrappers to break cache/collision issues
// Wrappers to break cache/collision issues
window.triggerComplete = function (id) {
    console.log("triggerComplete called", id);
    requestUpdateStatus(id, 'COMPLETADO');
};

window.triggerReschedule = function (id) {
    console.log("triggerReschedule called", id);
    pendingAction = null;
    openReschedule(id);
};

// Initialize Paste Listener
enableImagePaste();

// --- logic for Appointment Detail Modal ---
let currentTurnoIdDetail = null;

window.openTurnoDetails = async function (turnoId) {
    currentTurnoIdDetail = turnoId;
    try {
        const response = await fetch(`/turnos/${turnoId}/detalle`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error("No se pudo cargar el detalle del turno");
        const turno = await response.json();
        
        // Populate patient details
        const p = turno.paciente;
        document.getElementById('dt-paciente').textContent = p ? `${p.nombre} ${p.apellido}`.toUpperCase() : '-';
        document.getElementById('dt-dni').textContent = p ? p.dni : '-';
        document.getElementById('dt-obra-social').textContent = p && p.obra_social ? p.obra_social.nombre.toUpperCase() : '-';
        document.getElementById('dt-telefono').textContent = p ? (p.celular || p.telefono || '-') : '-';
        
        // Populate agenda details
        document.getElementById('dt-agenda').textContent = turno.agenda ? turno.agenda.nombre.toUpperCase() : '-';
        document.getElementById('dt-estado').textContent = turno.estado.toUpperCase();
        
        // Format date
        let dateStr = '-';
        if (turno.fecha) {
            const dateObj = new Date(turno.fecha);
            dateStr = dateObj.toLocaleDateString('es-AR');
        }
        document.getElementById('dt-fecha').textContent = dateStr;
        document.getElementById('dt-hora').textContent = turno.hora || '-';
        
        // Populate practices list
        const practicasContainer = document.getElementById('dt-practicas');
        practicasContainer.innerHTML = '';
        if (turno.practicas && turno.practicas.length > 0) {
            turno.practicas.forEach(pr => {
                const li = document.createElement('li');
                li.textContent = pr.nombre;
                practicasContainer.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.style.listStyle = 'none';
            li.style.color = '#a0aec0';
            li.textContent = 'Sin prácticas cargadas';
            practicasContainer.appendChild(li);
        }
        
        // Populate observations
        document.getElementById('dt-observaciones').value = turno.observaciones || '';
        
        // Open modal
        const modal = document.getElementById('detalleTurnoModal');
        if (modal) {
            modal.classList.add('active');
            modal.style.display = 'flex';
        }
    } catch (e) {
        console.error(e);
        alert("Error al cargar detalles del turno: " + e.message);
    }
}

window.closeDetalleTurnoModal = function () {
    const modal = document.getElementById('detalleTurnoModal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

window.saveTurnoObservaciones = async function () {
    if (!currentTurnoIdDetail) return;
    
    const obsValue = document.getElementById('dt-observaciones').value.trim();
    const btn = document.querySelector('#detalleTurnoModal .btn-primary');
    const originalText = btn.textContent;
    btn.textContent = 'Guardando...';
    btn.disabled = true;
    
    try {
        const response = await fetch(`/turnos/${currentTurnoIdDetail}`, {
            method: 'PATCH',
            headers: { 
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}` 
                
            },
            body: JSON.stringify({
                observaciones: obsValue || ""
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || "Error al actualizar las observaciones");
        }
        
        alert("Observaciones guardadas con éxito");
        closeDetalleTurnoModal();
        loadSlots(); // Refresh slot rendering to keep everything in sync
    } catch (e) {
        console.error(e);
        alert("Error al guardar: " + e.message);
    } finally {
        btn.textContent = originalText;
        btn.disabled = false;
    }
}
