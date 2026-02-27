import java.util.Arrays;
public class anagram {
    public static boolean isAnagram(String str1,String str2){
        if(str1.length()!=str2.length()){
            return false;
        }
        char[] ch1=str1.toCharArray();
        char[] ch2=str2.toCharArray();
        Arrays.sort(ch1);
        Arrays.sort(ch2);
        return Arrays.equals(ch1,ch2);
    }
    public static void main(String args[]){
        String str1="listen";
        String str2="silent";
        System.out.println(isAnagram(str1,str2));
    }
}