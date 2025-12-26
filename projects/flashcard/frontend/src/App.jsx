// frontend/src/App.jsx
import axios from 'axios';
import { useState } from 'react';

function App() {
  const [pdf, setPdf] = useState(null);
  const [flashcards, setFlashcards] = useState([]);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append("file", pdf);
    const res = await axios.post("http://localhost:8000/upload", formData);
    setFlashcards(res.data.flashcards);
  };

  return (
    <div className="p-4">
      <input type="file" onChange={e => setPdf(e.target.files[0])} />
      <button onClick={handleUpload}>Generate Flashcards</button>
      <ul>
        {flashcards.map((fc, idx) => <li key={idx}>{fc}</li>)}
      </ul>
    </div>
  );
}

export default App;
