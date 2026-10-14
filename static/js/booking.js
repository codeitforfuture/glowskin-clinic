document.addEventListener('DOMContentLoaded', function () {
  const dateInput = document.getElementById('date');
  const timeSelect = document.getElementById('time');
  const availabilityNote = document.getElementById('availabilityNote');
  if (!dateInput || !timeSelect) return;
  const ALL_SLOTS = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00', '14:30', '15:00', '15:30', '16:00', '16:30', '17:00', '17:30'];
  function populate(booked) {
    const current = timeSelect.value;
    timeSelect.innerHTML = '<option value="">Select a time</option>';
    ALL_SLOTS.forEach(slot => {
      const opt = document.createElement('option');
      opt.value = slot;
      opt.textContent = booked.includes(slot) ? slot + ' — Booked' : slot;
      if (booked.includes(slot)) opt.disabled = true;
      timeSelect.appendChild(opt);
    });
    if (current && !booked.includes(current)) timeSelect.value = current;
  }
  dateInput.addEventListener('change', () => {
    const date = dateInput.value;
    if (!date) { populate([]); availabilityNote.textContent = ''; return; }
    timeSelect.innerHTML = '<option value="">Loading…</option>';
    availabilityNote.textContent = 'Checking availability…';
    fetch('/api/availability?date=' + encodeURIComponent(date))
      .then(r => r.json())
      .then(data => {
        if (data.error) { availabilityNote.textContent = data.error; populate([]); return; }
        const booked = data.booked || [];
        populate(booked);
        const remaining = ALL_SLOTS.length - booked.length;
        if (remaining === 0) { availabilityNote.textContent = '❌ Fully booked. Try another day.'; availabilityNote.style.color = '#C0392B'; }
        else { availabilityNote.textContent = `✓ ${remaining} slot${remaining > 1 ? 's' : ''} available`; availabilityNote.style.color = '#2E7D32'; }
      })
      .catch(() => { availabilityNote.textContent = 'Could not load availability.'; populate([]); });
  });
  if (dateInput.value) dateInput.dispatchEvent(new Event('change'));
});