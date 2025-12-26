import axios from "axios";

export async function fetchIndianHeadlines() {
    // Using 'everything' endpoint with India-related queries since free tier doesn't support country parameter
    const url = `https://newsapi.org/v2/everything?q=India&sortBy=publishedAt&language=en&apiKey=${process.env.NEWSAPI_KEY}`;
    const { data } = await axios.get(url);

    return data.articles.slice(0, 20).map(a => ({
        title: a.title,
        source: a.source.name,
        url: a.url
    }));
}

export async function fetchStateNews(state) {
    const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(state + " India")}&sortBy=publishedAt&language=en&apiKey=${process.env.NEWSAPI_KEY}`;
    const { data } = await axios.get(url);

    return data.articles.slice(0, 10).map(a => ({
        title: a.title,
        source: a.source.name,
        url: a.url
    }));
}

// npm install -D tailwindcss postcss autoprefixer
