import axios from 'axios';
import { useState } from 'react';
import './App.css';

const App = () => {
  const [pdfFile, setPdfFile] = useState(null);
  const [flashcards, setFlashcards] = useState([]);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState({});
  const [flippedCards, setFlippedCards] = useState({});
  const [isLoading, setIsLoading] = useState(false);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setPdfFile(file);
    }
  };

  const handleGenerateFlashcards = async () => {
    if (!pdfFile) return alert('Please upload a PDF');

    setIsLoading(true);
    const formData = new FormData();
    formData.append('file', pdfFile);

    try {
      const res = await axios.post('http://localhost:8000/upload/', formData);
      setFlashcards(res.data.flashcards);
      setAnswers({});
      setResults({});
      setFlippedCards({});
    } catch (err) {
      console.error(err);
      alert('Error generating flashcards');
    } finally {
      setIsLoading(false);
    }
  };

  const handleMoreQuestions = async () => {
    setIsLoading(true);
    try {
      const res = await axios.get('http://localhost:8000/generate_more_flashcards/');
      setFlashcards((prev) => [...prev, ...res.data.flashcards]);
    } catch (err) {
      console.error(err);
      alert('Error generating more flashcards');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (index, value) => {
    setAnswers((prev) => ({
      ...prev,
      [index]: value
    }));
  };

  const handleSubmitAnswer = async (index) => {
    const question = flashcards[index].question;
    const userAnswer = answers[index];

    if (!userAnswer) return alert('Please enter an answer.');

    const formData = new FormData();
    formData.append('question', question);
    formData.append('answer', userAnswer);

    try {
      const res = await axios.post('http://localhost:8000/check-answer/', formData);
      setResults((prev) => ({
        ...prev,
        [index]: res.data.correct
      }));
      setFlippedCards((prev) => ({
        ...prev,
        [index]: true
      }));
    } catch (err) {
      console.error(err);
      alert('Error checking answer');
    }
  };

  const handleFlipBack = (index) => {
    setFlippedCards((prev) => ({
      ...prev,
      [index]: false
    }));
  };

  return (
    <div className="wrapper">
      <h1>Flashcard App</h1>

      <div className="controls">
        <label htmlFor="file-upload" className="btn upload-btn">
          {pdfFile ? pdfFile.name : 'Upload PDF'}
        </label>
        <input
          id="file-upload"
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
        />

        <button
          className="btn generate-btn"
          onClick={handleGenerateFlashcards}
          disabled={isLoading}
        >
          Generate Flashcards
        </button>

        <button
          className="btn generate-btn"
          onClick={handleMoreQuestions}
          disabled={isLoading}
        >
          Generate More Questions
        </button>
      </div>

      {isLoading && <p className="error">Processing... Please wait.</p>}

      <div className="grid">
        {flashcards.map((card, index) => (
          <div
            key={index}
            className={`card ${
              flippedCards[index] ? 'flipped' : ''
            } ${results[index] === true ? 'correct' : results[index] === false ? 'incorrect' : ''}`}
          >
            <div className="card-inner">
              <div className="card-front">
                <div>
                  <p><strong>Q{index + 1}:</strong> {card.question}</p>
                  <input
                    type="text"
                    placeholder="Your answer"
                    value={answers[index] || ''}
                    onChange={(e) => handleInputChange(index, e.target.value)}
                  />
                  <button className="check-btn" onClick={() => handleSubmitAnswer(index)}>
                    Submit
                  </button>
                </div>
              </div>

              <div className="card-back">
                <div>
                  {results[index] === true && <p>✅ Correct!</p>}
                  {results[index] === false && (
                    <p>❌ Incorrect<br />Correct Answer: {card.answer}</p>
                  )}
                  <button className="btn back-btn" onClick={() => handleFlipBack(index)}>
                    Back
                  </button>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default App;
