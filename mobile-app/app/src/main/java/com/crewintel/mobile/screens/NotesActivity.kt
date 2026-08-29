package com.crewintel.mobile.screens

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.crewintel.mobile.api.ApiClient
import com.crewintel.mobile.databinding.ActivityNotesBinding
import com.crewintel.mobile.databinding.ItemNoteBinding
import com.crewintel.mobile.models.Note
import com.crewintel.mobile.models.NoteRequest
import com.crewintel.mobile.models.NoteUpdateRequest
import com.crewintel.mobile.utils.PrefsManager
import kotlinx.coroutines.launch

class NotesActivity : AppCompatActivity() {

    private lateinit var binding: ActivityNotesBinding
    private lateinit var prefs: PrefsManager
    private val adapter = NoteAdapter(
        onDone = { id, done -> toggleDone(id, done) },
        onDelete = { id -> deleteNote(id) }
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityNotesBinding.inflate(layoutInflater)
        setContentView(binding.root)
        prefs = PrefsManager(this)

        binding.btnBack.setOnClickListener { finish() }
        binding.btnAdd.setOnClickListener { showAddDialog() }
        binding.rvNotes.layoutManager = LinearLayoutManager(this)
        binding.rvNotes.adapter = adapter

        loadNotes()
    }

    private fun loadNotes() {
        binding.progressBar.visibility = View.VISIBLE
        binding.tvEmpty.visibility = View.GONE
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val response = api.getNotes()
                if (response.isSuccessful) {
                    val notes = response.body() ?: emptyList()
                    if (notes.isEmpty()) {
                        binding.tvEmpty.visibility = View.VISIBLE
                    } else {
                        adapter.submitList(notes)
                    }
                }
            } catch (e: Exception) {
                Toast.makeText(this@NotesActivity, "Hata: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun showAddDialog() {
        val titleInput = EditText(this).apply {
            hint = "Not basligi"
            setPadding(48, 32, 48, 16)
            textSize = 16f
        }
        val bodyInput = EditText(this).apply {
            hint = "Not icerigi..."
            minLines = 3
            setPadding(48, 16, 48, 32)
            textSize = 14f
        }

        val layout = android.widget.LinearLayout(this).apply {
            orientation = android.widget.LinearLayout.VERTICAL
            setPadding(24, 16, 24, 0)
            addView(titleInput)
            addView(bodyInput)
        }

        val dialog = AlertDialog.Builder(this)
            .setTitle("Yeni Not")
            .setView(layout)
            .setPositiveButton("Kaydet", null)
            .setNegativeButton("Iptal", null)
            .create()

        dialog.setOnShowListener {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
                val title = titleInput.text.toString().trim()
                val body = bodyInput.text.toString().trim()
                if (title.isBlank()) {
                    Toast.makeText(this, "Lutfen baslik girin", Toast.LENGTH_SHORT).show()
                    return@setOnClickListener
                }
                dialog.dismiss()
                Toast.makeText(this, "Kaydediliyor...", Toast.LENGTH_SHORT).show()
                createNote(title, body)
            }
        }

        dialog.show()
    }

    private fun createNote(title: String, body: String) {
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                val note = NoteRequest(title = title, body = body, priority = "normal")
                val response = api.createNote(note)
                if (response.isSuccessful) {
                    Toast.makeText(this@NotesActivity, "Not kaydedildi", Toast.LENGTH_SHORT).show()
                    loadNotes()
                } else {
                    Toast.makeText(this@NotesActivity, "Hata: ${response.code()}", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@NotesActivity, "Kaydedilemedi: ${e.message}", Toast.LENGTH_LONG).show()
            }
        }
    }

    private fun toggleDone(id: Int, currentDone: Boolean) {
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                api.updateNote(id, NoteUpdateRequest(done = !currentDone))
                loadNotes()
            } catch (_: Exception) {}
        }
    }

    private fun deleteNote(id: Int) {
        lifecycleScope.launch {
            try {
                val api = ApiClient.getApi(prefs)
                api.deleteNote(id)
                loadNotes()
            } catch (_: Exception) {}
        }
    }
}

class NoteAdapter(
    private val onDone: (Int, Boolean) -> Unit,
    private val onDelete: (Int) -> Unit
) : androidx.recyclerview.widget.ListAdapter<Note, NoteAdapter.ViewHolder>(
    object : androidx.recyclerview.widget.DiffUtil.ItemCallback<Note>() {
        override fun areItemsTheSame(old: Note, new: Note) = old.id == new.id
        override fun areContentsTheSame(old: Note, new: Note) = old == new
    }
) {
    class ViewHolder(val binding: ItemNoteBinding) : RecyclerView.ViewHolder(binding.root)

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ViewHolder {
        val binding = ItemNoteBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return ViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ViewHolder, position: Int) {
        val note = getItem(position)

        holder.binding.tvTitle.text = note.title
        holder.binding.tvBody.text = note.body
        holder.binding.tvDate.text = note.createdAt.substringBefore("T")

        val color = when (note.priority) {
            "urgent" -> 0xFFEF4444.toInt()
            "high" -> 0xFFF97316.toInt()
            "normal" -> 0xFF3B82F6.toInt()
            else -> 0xFF94A3B8.toInt()
        }
        holder.binding.viewPriority.setBackgroundColor(color)

        if (note.done) {
            holder.binding.tvTitle.alpha = 0.5f
            holder.binding.tvBody.alpha = 0.5f
            holder.binding.btnDone.text = "↩"
        } else {
            holder.binding.tvTitle.alpha = 1.0f
            holder.binding.tvBody.alpha = 1.0f
            holder.binding.btnDone.text = "✓"
        }

        holder.binding.btnDone.setOnClickListener { onDone(note.id, note.done) }
        holder.binding.btnDelete.setOnClickListener { onDelete(note.id) }
    }
}
