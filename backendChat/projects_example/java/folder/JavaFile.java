import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.*;
import java.util.regex.*;

public class JavaFile {

    public static void main(String[] args) {
        String url = "https://en.wikipedia.org/wiki/Python_(programming_language)";
        String html = fetchHtml(url);

        if (html.isEmpty()) {
            System.out.println("Failed to fetch content.");
            return;
        }

        String text = stripHtmlTags(html);
        List<String> words = tokenize(text);
        Map<String, Integer> wordCounts = countWords(words);
        List<Map.Entry<String, Integer>> topWords = getTopWords(wordCounts, 10);

        System.out.println("\nTop 10 Most Common Words:");
        for (Map.Entry<String, Integer> entry : topWords) {
            System.out.println(entry.getKey() + ": " + entry.getValue());
        }
    }

    public static String fetchHtml(String urlStr) {
        StringBuilder content = new StringBuilder();

        try {
            URL url = new URL(urlStr);
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setRequestProperty("User-Agent", "Mozilla/5.0");
            BufferedReader in = new BufferedReader(
                new InputStreamReader(conn.getInputStream())
            );

            String line;
            while ((line = in.readLine()) != null) {
                content.append(line).append(" ");
            }
            in.close();
        } catch (Exception e) {
            System.out.println("Error fetching URL: " + e.getMessage());
        }

        return content.toString();
    }

    public static String stripHtmlTags(String html) {
        return html.replaceAll("(?s)<script.*?>.*?</script>", "")
                   .replaceAll("(?s)<style.*?>.*?</style>", "")
                   .replaceAll("<[^>]+>", " ")
                   .replaceAll("&[^;]+;", " ")
                   .replaceAll("\\s+", " ")
                   .toLowerCase();
    }

    public static List<String> tokenize(String text) {
        List<String> words = new ArrayList<>();
        Matcher matcher = Pattern.compile("\\b[a-z]+\\b").matcher(text);
        while (matcher.find()) {
            words.add(matcher.group());
        }
        return words;
    }

    public static Map<String, Integer> countWords(List<String> words) {
        Map<String, Integer> freq = new HashMap<>();
        for (String word : words) {
            freq.put(word, freq.getOrDefault(word, 0) + 1);
        }
        return freq;
    }

    public static List<Map.Entry<String, Integer>> getTopWords(Map<String, Integer> freq, int topN) {
        List<Map.Entry<String, Integer>> entries = new ArrayList<>(freq.entrySet());
        entries.sort((a, b) -> b.getValue().compareTo(a.getValue()));
        return entries.subList(0, Math.min(topN, entries.size()));
    }
}

//javac JavaFile.java && java JavaFile
