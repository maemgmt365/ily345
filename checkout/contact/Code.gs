// google apps script for the 345 support form. deploy as a web app (execute as me, anyone can access),
// then put the web app url in the worker secret CONTACT_URL and the same KEY below in CONTACT_KEY.
var KEY = 'c887c73688182d14f5eacf6dfdb09472c252ee255761ce27';
var TO = '345loveyours@gmail.com';

function doPost(e) {
  var d = {};
  try { d = JSON.parse(e.postData.contents || '{}'); } catch (err) {}
  if (!d.key || d.key !== KEY) return out({ ok: false, error: 'no' });
  var clean = function (v, n) { return String(v || '').replace(/[\u0000-\u001f]+/g, ' ').trim().slice(0, n); };
  var topic = clean(d.topic, 40) || 'other', name = clean(d.name, 80), email = clean(d.email, 120), order = clean(d.order, 60);
  var message = String(d.message || '').trim().slice(0, 1500);
  if (!name || !email || !message) return out({ ok: false, error: 'missing' });
  var subject = '345 support: ' + topic + (order ? ' (' + order + ')' : '') + ' from ' + name;
  var body = 'topic: ' + topic + '\nname: ' + name + '\nemail: ' + email + '\norder: ' + (order || '-') + '\npage: ' + clean(d.page, 200) + '\n\n' + message;
  MailApp.sendEmail({ to: TO, replyTo: email, subject: subject, body: body, name: '345 support' });
  return out({ ok: true });
}
function out(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
