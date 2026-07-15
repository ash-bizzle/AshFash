import { useState } from 'react';

export default function SearchBar({ value, onSearch }) {
  const [input, setInput] = useState(value || '');

  const submit = (e) => {
    e.preventDefault();
    onSearch(input.trim());
  };

  return (
    <form onSubmit={submit} style={styles.form}>
      <input
        type="text"
        placeholder="Search products..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        style={styles.input}
      />
      <button type="submit" style={styles.btn}>Search</button>
      {value && (
        <button type="button" style={styles.clearBtn} onClick={() => { setInput(''); onSearch(''); }}>
          ✕
        </button>
      )}
    </form>
  );
}

const styles = {
  form: { display: 'flex', gap: 8, alignItems: 'center' },
  input: {
    flex: 1,
    padding: '10px 14px',
    fontSize: 14,
    border: '1px solid #ddd',
    borderRadius: 6,
    outline: 'none',
    maxWidth: 400,
  },
  btn: {
    padding: '10px 20px',
    background: '#222',
    color: '#fff',
    border: 'none',
    borderRadius: 6,
    fontSize: 14,
    cursor: 'pointer',
  },
  clearBtn: {
    background: 'none',
    border: 'none',
    fontSize: 16,
    cursor: 'pointer',
    color: '#888',
  },
};
